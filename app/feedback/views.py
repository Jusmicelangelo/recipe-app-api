"""
Views for FeedbackInvitation APIs.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import FeedbackInvitation, Feedback, PersonalityTrait, TalentCategory, Talent
from .serializers import FeedbackInvitationSerializer, PersonalityTraitSerializer, TalentCategorySerializer, FeedbackSerializer


class FeedbackInvitationViewSet(viewsets.ModelViewSet):
    """View for manage FeedbackInvitation APIs."""
    queryset = FeedbackInvitation.objects.all()
    serializer_class = FeedbackInvitationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(inviter=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(FeedbackInvitationSerializer(instance).data, status=status.HTTP_200_OK)


@api_view(["POST"])
def accept_invitation(request, invite_id):
    """Mark the invitation as used."""
    invitation = get_object_or_404(FeedbackInvitation, id=invite_id, used=False)
    invitation.used = True
    invitation.save()
    return Response({"message": "Invitation accepted!"}, status=200)

@extend_schema(
    request=FeedbackSerializer,
    responses={201: FeedbackSerializer, 400: "Invalid request"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def submit_feedback(request, invite_id):
    """
    API for invited users to submit feedback with radar chart, personality traits, and talents.
    """
    invitation = get_object_or_404(FeedbackInvitation, id=invite_id, used=True)

    if hasattr(invitation, "feedback"):
        return Response({"error": "Feedback already submitted"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = FeedbackSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(invitation=invitation)
        return Response (serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([AllowAny])
def list_personality_traits(request):
    """
    API to fetch all available personality traits"""
    categories = PersonalityTrait.objects.all()
    serializer = PersonalityTraitSerializer(categories, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([AllowAny])
def list_talent_categories(request):
    """
    API to fetch all talent categories along with their talents.
    """
    categories = TalentCategory.objects.all()
    serializer = TalentCategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([])
def get_talent_category(request, category_id):
    """
    Retrieve all available talent categories with their talents.
    """
    categories = TalentCategory.objects.prefetch_related("talents").all()
    serializer = TalentCategorySerializer(categories, many=True)
    return Response(serializer.data)