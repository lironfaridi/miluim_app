from datetime import timedelta, date
from Tabels import engine, Role, Soldier, PlatoonRequirement, LeaveRecord, sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

def get_role_counts_for_date(platoon_number, target_date):
    """מחשבת כמה אנשים מכל תפקיד נמצאים בבסיס בתאריך ספציפי"""
    all_soldiers = session.query(Soldier).filter_by(platoon_number=platoon_number, is_active=True).all()

    # מי בבית בתאריך הזה?
    soldiers_at_home_ids = session.query(LeaveRecord.soldier_id).filter(
        LeaveRecord.start_date <= target_date,
        LeaveRecord.end_date >= target_date
    ).all()
    soldiers_at_home_ids = [s[0] for s in soldiers_at_home_ids]

    counts = {}
    for s in all_soldiers:
        if s.id not in soldiers_at_home_ids:
            for role in s.roles:
                counts[role.name] = counts.get(role.name, 0) + 1
    return counts

def add_leave_request(soldier_name, start_date, end_date, is_mandatory=False):
    """בודקת יציאה לטווח תאריכים ורושמת ב-DB אם תקין, תוך התחשבות בחפיפות"""
    soldier = session.query(Soldier).filter_by(name=soldier_name).first()
    if not soldier: return "חייל לא נמצא"

    # לוגיקת חפיפה: בודקים כשירות קשיחה רק על הימים שבין היציאה לחזרה
    # יום היציאה ויום החזרה נחשבים ימי חילופים (חפיפה)
    check_start = start_date + timedelta(days=1)
    check_end = end_date - timedelta(days=1)

    current_date = check_start
    while current_date <= check_end:
        counts = get_role_counts_for_date(soldier.platoon_number, current_date)

        # הפחתה וירטואלית של החייל המבקש
        for role in soldier.roles:
            counts[role.name] = counts.get(role.name, 0) - 1

        # בדיקה מול דרישות המינימום
        reqs = session.query(PlatoonRequirement).filter_by(platoon_number=soldier.platoon_number).all()
        for r in reqs:
            role_name = session.get(Role, r.role_id).name
            if counts.get(role_name, 0) < r.min_required and not is_mandatory:
                return f"❌ התנגשות ב-{current_date.strftime('%d/%m')}: חסר {role_name} (יום מלא בבית)"

        current_date += timedelta(days=1)

    # אם עברנו את בדיקת ימי האמצע - רושמים ב-DB
    new_leave = LeaveRecord(soldier_id=soldier.id, start_date=start_date, end_date=end_date, is_mandatory=is_mandatory)
    session.add(new_leave)
    session.commit()
    return f"✅ נרשם: {soldier_name} מ-{start_date.strftime('%d/%m')} עד {end_date.strftime('%d/%m')} (כולל ימי חפיפה)"

# --- אזור הטסטים ---
if __name__ == "__main__":
    # בדיקת חפיפה: ישראל ודניאל יוצאים/חוזרים באותו יום
    print("\n--- טסט חפיפה: דניאל יוצא ב-3.4, ישראל חוזר ב-3.4 ---")
    # נניח שישראל כבר רשום כחוזר ב-3.4, דניאל ינסה לצאת ב-3.4
    # המערכת תאשר כי 3.4 הוא יום חפיפה עבור דניאל
    res = add_leave_request("דניאל לוי", date(2026, 4, 3), date(2026, 4, 7))
    print(res)