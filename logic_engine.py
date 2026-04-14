from datetime import timedelta, date
from Tabels import engine, Role, Soldier, PlatoonRequirement, LeaveRecord, sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

def get_role_counts_for_date(platoon_number, target_date):
    """מחשבת כמה אנשים מכל תפקיד נמצאים בבסיס בתאריך ספציפי"""
    # 1. כל החיילים במחלקה
    all_soldiers = session.query(Soldier).filter_by(platoon_number=platoon_number, is_active=True).all()

    # 2. מי בבית בתאריך הזה?
    soldiers_at_home_ids = session.query(LeaveRecord.soldier_id).filter(
        LeaveRecord.start_date <= target_date,
        LeaveRecord.end_date >= target_date
    ).all()
    soldiers_at_home_ids = [s[0] for s in soldiers_at_home_ids]

    # 3. ספירת תפקידים של מי שנשאר בבסיס
    counts = {}
    for s in all_soldiers:
        if s.id not in soldiers_at_home_ids:
            for role in s.roles:
                counts[role.name] = counts.get(role.name, 0) + 1
    return counts

def add_leave_request(soldier_name, start_date, end_date, is_mandatory=False):
    """בודקת יציאה לטווח תאריכים ורושמת ב-DB אם תקין"""
    soldier = session.query(Soldier).filter_by(name=soldier_name).first()
    if not soldier: return "חייל לא נמצא"

    # מעבר על כל יום בטווח
    current_date = start_date
    while current_date <= end_date:
        counts = get_role_counts_for_date(soldier.platoon_number, current_date)

        # הפחתה וירטואלית של החייל המבקש
        for role in soldier.roles:
            counts[role.name] = counts.get(role.name, 0) - 1

        # בדיקה מול דרישות
        reqs = session.query(PlatoonRequirement).filter_by(platoon_number=soldier.platoon_number).all()
        for r in reqs:
            role_name = session.get(Role, r.role_id).name
            if counts.get(role_name, 0) < r.min_required and not is_mandatory:
                return f"❌ התנגשות בתאריך {current_date.strftime('%d/%m/%Y')}: חסר {role_name}"

        current_date += timedelta(days=1)

    # אם הגענו לכאן - הכל תקין, רושמים ב-DB
    new_leave = LeaveRecord(soldier_id=soldier.id, start_date=start_date, end_date=end_date, is_mandatory=is_mandatory)
    session.add(new_leave)
    session.commit()
    return f"✅ היציאה של {soldier_name} נרשמה בהצלחה מ-{start_date.strftime('%d/%m/%Y')} עד {end_date.strftime('%d/%m/%Y')}!"

# --- אזור הטסטים ---
if __name__ == "__main__":
    print("\n--- טסט 1: מוציאים את דניאל מראשון עד שלישי (1.5.2026 - 3.5.2026) ---")
    result1 = add_leave_request("דניאל לוי", date(2026, 5, 1), date(2026, 5, 3))
    print(result1)

    print("\n--- טסט 2: מנסים להוציא את ישראל באותם תאריכים ---")
    result2 = add_leave_request("ישראל ישראלי", date(2026, 5, 1), date(2026, 5, 3))
    print(result2)