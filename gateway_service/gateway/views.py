from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Create your views here.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_protect(request):
    return Response({'message':f"Hello {request.user.username}, you're authenticated!"})