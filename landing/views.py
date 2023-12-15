from .models import UserAuth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from hv_back.utils import log_user_action  

class LoginView(APIView):
    def post(self, request):
        subsr = request.data.get('subsr')
        use_ip = request.data.get('use_ip')
        user_auth = UserAuth.objects.filter(subsr=subsr, use_ip=use_ip).first()
        try:
            if user_auth:
                refresh = RefreshToken.for_user(user_auth)
                token = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'subsr': subsr,
                }
                response = Response(token, status=status.HTTP_200_OK)
            else:
                response = Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            response = Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if response:
                log_user_action(subsr, request, response)  # 로그 기록
            return response