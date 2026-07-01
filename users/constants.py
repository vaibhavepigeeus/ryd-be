class UserRole:
    ADMIN = "admin"
    COACH = "coach"
    COACHEE = "coachee"

    CHOICES = (
        (ADMIN, "Admin"),
        (COACH, "Coach"),
        (COACHEE, "Coachee"),
    )

    ALL = {ADMIN, COACH, COACHEE}


class UserStatus:
    ACTIVE = "Active"
    INACTIVE = "Inactive"
