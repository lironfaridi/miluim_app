import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import io
from Tabels import sessionmaker, engine, Soldier, Role, PlatoonRequirement, LeaveRecord
from logic_engine import add_leave_request

st.set_page_config(page_title="מערכת שליטה פלוגתית", page_icon="🛡️", layout="wide")

# חיבור למסד הנתונים
Session = sessionmaker(bind=engine)
session = Session()


# פונקציות עזר
def get_all_roles():
    return session.query(Role).all()


# --- סרגל צד (Sidebar) לסינון גלובלי ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("ניהול פלוגה")

    # רשימת המחלקות המוגדרות בפלוגה
    platoon_options = ["מרגמות", "אוהד", "ניוד"]
    selected_platoon = st.selectbox("בחר מחלקה לצפייה:", platoon_options)

    st.divider()
    st.info(f"מציג נתונים עבור מחלקה: {selected_platoon}")

# --- תפריט עליון בלשוניות ---
tab1, tab2, tab3 = st.tabs(["📅 לוח יציאות (Gantt)", "👤 ניהול כוח אדם", "⚙️ הגדרות מחלקה"])

# --- לשונית 1: לוח יציאות וגאנט ---
with tab1:
    st.header(f"מפת יציאות - מחלקה {selected_platoon}")
    col_form, col_graph = st.columns([1, 3])

    with col_form:
        st.subheader("רישום יציאה")
        platoon_soldiers = session.query(Soldier).filter_by(platoon_number=selected_platoon, is_active=True).all()
        s_names = [s.name for s in platoon_soldiers]

        if not s_names:
            st.warning(f"אין חיילים במחלקת {selected_platoon}. הוסף אותם בטאב ניהול כוח אדם.")
        else:
            with st.form("leave_form"):
                sel_s = st.selectbox("חייל:", s_names)
                d_start = st.date_input("מהתאריך:", value=date.today())
                d_end = st.date_input("עד התאריך:", value=date.today())
                mandatory = st.checkbox("אילוץ קשיח ⚠️")
                if st.form_submit_button("בדוק ושמור"):
                    res = add_leave_request(sel_s, d_start, d_end, mandatory)
                    if "✅" in res:
                        st.success(res)
                        st.rerun()
                    else:
                        st.error(res)

    with col_graph:
        leaves = session.query(LeaveRecord).join(Soldier).filter(Soldier.platoon_number == selected_platoon).all()
        if leaves:
            df = pd.DataFrame([{
                "חייל": l.soldier.name,
                "התחלה": l.start_date,
                "סיום": l.end_date,
                "טקסט": f"{l.start_date.strftime('%d/%m')} - {l.end_date.strftime('%d/%m')}"
            } for l in leaves])

            fig = px.timeline(df, x_start="התחלה", x_end="סיום", y="חייל", color="חייל",
                              text="טקסט", template="plotly_white")
            fig.update_traces(textposition='inside', insidetextanchor='middle')
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

            export_df = df[['חייל', 'התחלה', 'סיום']].copy()
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name='לוח יציאות')

            st.download_button(
                label="📥 הורד לוח יציאות (Excel)",
                data=buffer.getvalue(),
                file_name=f"leaves_{selected_platoon}_{date.today()}.xlsx",
                mime="application/vnd.ms-excel"
            )

            with st.expander("🗑️ מחיקת יציאות קיימות"):
                for l in leaves:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"{l.soldier.name}: {l.start_date} עד {l.end_date}")
                    if c2.button("מחק", key=f"del_{l.id}"):
                        session.delete(l)
                        session.commit()
                        st.rerun()
        else:
            st.info(f"אין יציאות רשומות כרגע למחלקת {selected_platoon}.")

# --- לשונית 2: ניהול כוח אדם ---
with tab2:
    st.header(f"ניהול סד\"כ - {selected_platoon}")
    col_add, col_edit = st.columns(2)
    with col_add:
        st.subheader("➕ הוספת חייל")
        with st.form("add_soldier"):
            new_name = st.text_input("שם מלא:")
            # המחלקה נקבעת אוטומטית לפי הבחירה ב-Sidebar
            platoon = st.text_input("מחלקה:", value=selected_platoon, disabled=True)
            all_r = [r.name for r in get_all_roles()]
            sel_r = st.multiselect("תפקידים:", all_r)
            if st.form_submit_button("הוסף"):
                if new_name:
                    s = Soldier(name=new_name, platoon_number=selected_platoon)
                    for rn in sel_r:
                        s.roles.append(session.query(Role).filter_by(name=rn).first())
                    session.add(s)
                    session.commit()
                    st.success("נוסף בהצלחה")
                    st.rerun()

    with col_edit:
        st.subheader("📝 עריכת חייל קיים")
        all_s = session.query(Soldier).filter_by(platoon_number=selected_platoon).all()
        if all_s:
            edit_s_name = st.selectbox("בחר חייל לעריכה:", [s.name for s in all_s])
            edit_s_obj = session.query(Soldier).filter_by(name=edit_s_name).first()
            with st.form("edit_form"):
                up_name = st.text_input("שם מעודכן:", value=edit_s_obj.name)
                # אפשרות להעביר חייל בין מחלקות
                up_platoon = st.selectbox("מחלקה מעודכנת:", platoon_options,
                                          index=platoon_options.index(edit_s_obj.platoon_number))
                curr_roles = [r.name for r in edit_s_obj.roles]
                all_r_names = [r.name for r in get_all_roles()]
                up_roles = st.multiselect("תפקידים מעודכנים:", all_r_names, default=curr_roles)
                if st.form_submit_button("שמור שינויים"):
                    edit_s_obj.name = up_name
                    edit_s_obj.platoon_number = up_platoon
                    edit_s_obj.roles = []
                    for rn in up_roles:
                        edit_s_obj.roles.append(session.query(Role).filter_by(name=rn).first())
                    session.commit()
                    st.success("עודכן בהצלחה")
                    st.rerun()
        else:
            st.write(f"אין חיילים לעריכה במחלקת {selected_platoon}.")

# --- לשונית 3: הגדרות מחלקה ---
with tab3:
    st.header(f"⚙️ הגדרות וכשירות - מחלקת {selected_platoon}")

    # הוספת תפקיד חדש למערכת הפלוגתית
    with st.expander("➕ הוספת תפקיד חדש למערכת"):
        with st.form("add_role_sys"):
            new_r_name = st.text_input("שם התפקיד (למשל: מפעיל אמצעי, נהג כבד):")
            if st.form_submit_button("הוסף תפקיד למאגר"):
                if new_r_name and not session.query(Role).filter_by(name=new_r_name).first():
                    session.add(Role(name=new_r_name))
                    session.commit()
                    st.success(f"התפקיד '{new_r_name}' נוסף למאגר. כעת ניתן לקבוע לו מינימום.")
                    st.rerun()

    st.divider()

    # ניהול המינימום למחלקה הנוכחית
    reqs = session.query(PlatoonRequirement).filter_by(platoon_number=selected_platoon).all()

    # אם חסרים תפקידים בדרישות של המחלקה הזו, נוסיף אותם עם מינימום 0
    all_system_roles = get_all_roles()
    existing_role_ids = [r.role_id for r in reqs]
    for r in all_system_roles:
        if r.id not in existing_role_ids:
            session.add(PlatoonRequirement(platoon_number=selected_platoon, role_id=r.id, min_required=0))
    session.commit()

    # שליפה מחדש אחרי עדכון
    reqs = session.query(PlatoonRequirement).filter_by(platoon_number=selected_platoon).all()

    st.subheader("קביעת מינימום בבסיס:")
    col_a, col_b = st.columns(2)
    for i, r in enumerate(reqs):
        role_n = session.get(Role, r.role_id).name
        target_col = col_a if i % 2 == 0 else col_b
        new_val = target_col.number_input(f"מינימום {role_n}:", min_value=0, value=r.min_required, key=f"set_{r.id}")
        if new_val != r.min_required:
            r.min_required = new_val
            session.commit()
            st.toast(f"עודכן מינימום ל-{role_n}")