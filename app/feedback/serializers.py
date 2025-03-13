from rest_framework import serializers
from .models import FeedbackInvitation, PersonalityTrait, TalentCategory, Talent, Feedback

class FeedbackInvitationSerializer(serializers.ModelSerializer):
    """Serializer for Feedback Invitation."""
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackInvitation
        fields = ["id", "inviter", "invitee_email", "used", "created_at", "qr_code"]
        read_only_fields = ["id", "inviter", "used", "created_at", "qr_code"]

    def validate_invitee_email(self, value):
        if FeedbackInvitation.objects.filter(invitee_email=value).exists():
            raise serializers.ValidationError("An invitation has already been sent to this email.")
        return value

    def get_qr_code(self, obj):
        """Generating a QR code."""
        from .utils import generate_qr_code
        return generate_qr_code(obj.id)


class PersonalityTraitSerializer(serializers.ModelSerializer):
    """Serializer for Personality Traits."""
    class Meta:
        model = PersonalityTrait
        fields = ["id", "name"]


class TalentSerializer(serializers.ModelSerializer):
    """Serializer for Talent."""
    class Meta:
        model = Talent
        fields = ["id", "name"]


class TalentCategorySerializer(serializers.ModelSerializer):
    """Serializer for Talent Category."""
    talents = TalentSerializer(many=True, read_only=True)
    class Meta:
        model = TalentCategory
        fields = ["id", "name", "talents"]


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for Feedback"""
    personality_traits = serializers.PrimaryKeyRelatedField(
        queryset=PersonalityTrait.objects.all(), many=True, required=False
    )
    talents = serializers.PrimaryKeyRelatedField(
        queryset=Talent.objects.all(), many=True, required=False
    )
    class Meta:
        model = Feedback
        fields = [
            "id", "invitation", "name", "email", "feedback_type",
            "category_driving", "category_exploring", "category_understanding", "category_communicating",
            "personality_traits", "talents", "created_at"
        ]
        read_only_fields = ["id", "created_at", "invitation"]

    def validate(self, data):
        try:
            # Ensure category values are integers
            category_driving = int(data.get("category_driving", 0))
            category_exploring = int(data.get("category_exploring", 0))
            category_understanding = int(data.get("category_understanding", 0))
            category_communicating = int(data.get("category_communicating", 0))
        except ValueError:
            raise serializers.ValidationError({"non_field_errors": ["Category values must be integers."]})
        total = category_driving + category_exploring + category_communicating + category_understanding
        if total != 14:
            raise serializers.ValidationError({"non_field_errors": ["The total sum of category values must be exactly 14."]})
        return data
