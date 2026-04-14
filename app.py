import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import io
from Tabels import sessionmaker, engine, Soldier, Role, PlatoonRequirement, LeaveRecord
from logic_engine import add_leave_request, get_role_counts_for_date

# הגדרות דף מתקדמות
st.set_page_config(page_title="מערכת אופטימיזציה פלוגתית", page_icon="🛡️", layout="wide")

# חיבור למסד הנתונים
Session = sessionmaker(bind=engine)
session = Session()

# פונקציות עזר
def get_all_roles():
    return session.query(Role).all()

# --- סרגל צד (Sidebar) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("Resource Control")
    platoon_options = ["מרגמות", "אוהד", "ניוד"]
    selected_platoon = st.selectbox("בחר יחידה תפעולית:", platoon_options)
    st.divider()
    st.success(f"מחלקה פעילה: {selected_platoon}")

# --- טאב 1: לוח משימות ואופטימיזציה ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Gantt", "👤 ניהול סד\"כ", "⚙️ הגדרות אילוצים"])

with tab1:
    st.title(f"ניהול כשירות - מחלקת {selected_platoon}")

    # --- חלק 1: Dashboard KPIs ---
    platoon_soldiers = session.query(Soldier).filter_by(platoon_number=selected_platoon, is_active=True).all()
    today_counts = get_role_counts_for_date(selected_platoon, date.today())

    # חישוב כשירות כללית
    is_fully_ready = True
    reqs = session.query(PlatoonRequirement).filter_by(platoon_number=selected_platoon).all()
    for r in reqs:
        role_n = session.get(Role, r.role_id).name
        if today_counts.get(role_n, 0) < r.min_required:
            is_fully_ready = False
            break

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("סה\"כ סד\"כ פעיל", len(platoon_soldiers))

    at_home = session.query(LeaveRecord).join(Soldier).filter(
        Soldier.platoon_number == selected_platoon,
        LeaveRecord.start_date <= date.today(),
        LeaveRecord.end_date >= date.today()
    ).count()
    kpi2.metric("חיילים מחוץ ליחידה", at_home, delta=f"{at_home} בבית", delta_color="inverse")

    status_text = "כשירות מלאה ✅" if is_fully_ready else "חריגת כשירות ⚠️"
    kpi3.metric("סטטוס אילוצים", status_text)

    st.divider()

    # --- חלק 2: רישום וגאנט ---
    col_form, col_graph = st.columns([1, 2.5])

    with col_form:
        with st.container(border=True):
            st.markdown("### 📝 הזנת יציאה חדשה")
            s_names = [s.name for s in platoon_soldiers]
            if not s_names:
                st.warning("יש להזין חיילים במערכת.")
            else:
                with st.form("leave_form", clear_on_submit=True):
                    sel_s = st.selectbox("חייל:", s_names)
                    d_start = st.date_input("תאריך יציאה:", value=date.today())
                    d_end = st.date_input("תאריך חזרה:", value=date.today() + timedelta(days=2))
                    mandatory = st.checkbox("אילוץ קשיח (חריגת מפקד) ⚠️")

                    if st.form_submit_button("בדוק אילוצים ואשר", type="primary", use_container_width=True):
                        res = add_leave_request(sel_s, d_start, d_end, mandatory)
                        if "✅" in res:
                            st.success(res, icon="🎉")
                            st.rerun()
                        else:
                            st.error(f"**חסימת אילוץ:**\n{res}", icon="🚨")

    with col_graph:
        leaves = session.query(LeaveRecord).join(Soldier).filter(Soldier.platoon_number == selected_platoon).all()
        if leaves:
            df = pd.DataFrame([{
                "חייל": l.soldier.name,
                "התחלה": l.start_date,
                "סיום": l.end_date,
                "תצוגה": f"{l.start_date.strftime('%d/%m')} - {l.end_date.strftime('%d/%m')}"
            } for l in leaves])

            fig = px.timeline(df, x_start="התחלה", x_end="סיום", y="חייל", color="חייל",
                              text="תצוגה", template="plotly_white", title="מפת פריסת כוח אדם")

            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#f0f0f0', title="ציר זמן"),
                yaxis=dict(showgrid=False, title=""),
                margin=dict(l=0, r=0, t=40, b=0),
                showlegend=False,
                height=450
            )
            fig.update_traces(textposition='inside', insidetextanchor='middle', marker_line_width=0, opacity=0.85)
            st.plotly_chart(fig, use_container_width=True)

            # ייצוא
            export_df = df[['חייל', 'התחלה', 'סיום']].copy()
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False)

            st.download_button("📥 ייצוא לדו\"ח אקסל", buffer.getvalue(),
                               file_name=f"report_{selected_platoon}.xlsx", type="secondary")

            # --- הוספת מנגנון המחיקה שהושמט ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🗑️ ניהול ומחיקת רשומות קיימות"):
                for l in leaves:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"**{l.soldier.name}** | {l.start_date.strftime('%d/%m')} עד {l.end_date.strftime('%d/%m')}")
                    if c2.button("מחק", key=f"del_{l.id}"):
                        session.delete(l)
                        session.commit()
                        st.rerun()
            # -----------------------------------
        else:
            st.info("אין נתונים להצגה על ציר הזמן.")

# --- טאב 2: ניהול סד"כ ---
with tab2:
    st.header(f"ניהול משאבי אנוש - {selected_platoon}")
    col_add, col_edit = st.columns(2)

    with col_add:
        with st.container(border=True):
            st.subheader("➕ הוספת חייל למערכת")
            with st.form("add_soldier"):
                new_name = st.text_input("שם מלא:")
                all_r = [r.name for r in get_all_roles()]
                sel_r = st.multiselect("שיוך תפקידים ומיומנויות:", all_r)
                if st.form_submit_button("שמור חייל", type="primary"):
                    if new_name:
                        s = Soldier(name=new_name, platoon_number=selected_platoon)
                        for rn in sel_r:
                            s.roles.append(session.query(Role).filter_by(name=rn).first())
                        session.add(s)
                        session.commit()
                        st.success(f"החייל {new_name} נקלט בהצלחה")
                        st.rerun()

    with col_edit:
        with st.container(border=True):
            st.subheader("📝 עדכון פרטי עובד")
            all_s = session.query(Soldier).filter_by(platoon_number=selected_platoon).all()
            if all_s:
                edit_s_name = st.selectbox("בחר חייל:", [s.name for s in all_s])
                edit_s_obj = session.query(Soldier).filter_by(name=edit_s_name).first()
                with st.form("edit_form"):
                    up_name = st.text_input("שם מעודכן:", value=edit_s_obj.name)
                    up_platoon = st.selectbox("העברה למחלקה:", platoon_options,
                                              index=platoon_options.index(edit_s_obj.platoon_number))
                    curr_roles = [r.name for r in edit_s_obj.roles]
                    up_roles = st.multiselect("תפקידים מעודכנים:", [r.name for r in get_all_roles()],
                                              default=curr_roles)
                    if st.form_submit_button("עדכן נתונים"):
                        edit_s_obj.name = up_name
                        edit_s_obj.platoon_number = up_platoon
                        edit_s_obj.roles = [session.query(Role).filter_by(name=rn).first() for rn in up_roles]
                        session.commit()
                        st.rerun()

# --- טאב 3: הגדרות אילוצים ---
with tab3:
    st.header(f"⚙️ הגדרת אילוצים מבצעיים - {selected_platoon}")

    with st.expander("🛠️ ניהול תשתית תפקידים פלוגתית"):
        new_r_name = st.text_input("הוסף תפקיד חדש למאגר:")
        if st.button("אשר הוספת תפקיד"):
            if new_r_name and not session.query(Role).filter_by(name=new_r_name).first():
                session.add(Role(name=new_r_name))
                session.commit()
                st.rerun()

    st.divider()

    # הבטחת קיום דרישות לכל התפקידים (אוטומציה)
    all_system_roles = get_all_roles()
    for r in all_system_roles:
        if not session.query(PlatoonRequirement).filter_by(platoon_number=selected_platoon, role_id=r.id).first():
            session.add(PlatoonRequirement(platoon_number=selected_platoon, role_id=r.id, min_required=0))
    session.commit()

    st.subheader("קביעת רף מינימום להפעלת היחידה:")
    reqs = session.query(PlatoonRequirement).filter_by(platoon_number=selected_platoon).all()
    col_a, col_b = st.columns(2)
    for i, r in enumerate(reqs):
        role_n = session.get(Role, r.role_id).name
        target_col = col_a if i % 2 == 0 else col_b
        new_val = target_col.number_input(f"מינימום {role_n}:", min_value=0, value=r.min_required, key=f"set_{r.id}")
        if new_val != r.min_required:
            r.min_required = new_val
            session.commit()
            st.toast(f"אילוץ {role_n} עודכן")