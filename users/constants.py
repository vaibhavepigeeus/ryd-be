class UserRole:
    COACH = "coach"
    COACHEE = "coachee"

    CHOICES = (
        (COACH, "Coach"),
        (COACHEE, "Coachee"),
    )

    ALL = {COACH, COACHEE}


class UserStatus:
    ACTIVE = "Active"
    INACTIVE = "Inactive"
