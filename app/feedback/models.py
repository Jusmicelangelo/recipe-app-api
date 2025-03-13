import uuid
from core.models import User
from django.db import models


# ✅ Quality model (Acts as a category for personality traits)
class Quality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

# ✅ Personality Trait model (Linked to a specific Quality)
class PersonalityTrait(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    quality = models.ForeignKey(
        "Quality",
        on_delete=models.CASCADE,
        related_name="traits",
        to_field="id",
        db_column="quality_id"
    )

    def __str__(self):
        return self.name

class TalentCategory(models.Model):
    """
    Groups talents into categories -- HAS TO BE EXCERPTED TO SEPARATE APP.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Talent(models.Model):
    """
    Represents an individual talent belonging to a category.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(
        "TalentCategory",
        on_delete=models.CASCADE,
        to_field="id",
        related_name="talents",
        db_column="category_id"
    )


    def __str__(self):
        return f"{self.name} ({self.category.name})"


class FeedbackInvitation(models.Model):
    """Feedback Invitation Object."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations")
    invitee_email = models.EmailField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation from {self.inviter} to {self.invitee_email}"


class Feedback(models.Model):
    """Feedback Object."""
    FEEDBACK_CHOICES = [
        ("quick", "Quick"),
        ("advanced", "Advanced"),
    ]
    invitation = models.OneToOneField("FeedbackInvitation", on_delete=models.CASCADE, related_name="feedback")
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Radar Chart Inputs (4 categories, total must be 14)
    category_driving = models.PositiveBigIntegerField(default=0)
    category_exploring = models.PositiveBigIntegerField(default=0)
    category_understanding = models.PositiveBigIntegerField(default=0)
    category_communicating = models.PositiveBigIntegerField(default=0)

    # After the 14 score spend decide to only go for talent feedback or talent and personality trait feedback
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, default="Advanced")

    # New Multi-Select for Personality Traits and Talents
    personality_traits = models.ManyToManyField(PersonalityTrait, blank=True)
    talents = models.ManyToManyField(Talent, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        total = self.category_driving + self.category_exploring + self.category_understanding + self.category_communicating
        if total != 14:
            raise ValueError("The sum of the personality traits scores must be exactly 14 points.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Feedback ({self.feedback_type}) from {self.invitation.invitee_email}"


