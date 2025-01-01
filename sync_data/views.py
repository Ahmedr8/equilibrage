from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import ParamSynchro, SyncLog
from .services import AuthenticationRfeService
from .serializers import ParamSynchroSerializer, SyncLogSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ParamSynchro
from .serializers import ParamSynchroSerializer


@method_decorator(csrf_exempt, name='dispatch')
class SyncFilesView(APIView):
    def post(self, request):
        print("Received sync request with data:", request.data)
        destination_path = "./files"
        api_spec=request.data.pop('api_spec')

        workspace = request.data.get('workspace')
        username = request.data.get('username')
        password = request.data.get('password')
        environment = request.data.get('environment')
        container_name = request.data.get('container_name')
        path = request.data.get('path')
        # Create the ParamSynchro instance
        param_synchro = ParamSynchro(
            workspace=workspace,
            username=username,
            password=password,
            environment=environment,
            container_name=container_name,
            path=path
        )

        service = AuthenticationRfeService()
        success = service.download_files_from_folder(param_synchro, destination_path,api_spec)

        if success.status:
            response_data = {
                'status': 'success',
                'message': 'Files downloaded and processed successfully',
                'sync_logs': SyncLogSerializer(success.log).data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = {
                'status': 'error',
                'message': 'Failed to download files :'+SyncLogSerializer(success.log).data["error_message"],
                'sync_logs': SyncLogSerializer(success.log).data
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParamSynchroViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = ParamSynchroSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        param = get_object_or_404(ParamSynchro, workspace=pk)
        serializer = ParamSynchroSerializer(param)
        return Response(serializer.data)

    def list(self, request):
        params = ParamSynchro.objects.all()
        serializer = ParamSynchroSerializer(params, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        param = get_object_or_404(ParamSynchro, workspace=pk)
        serializer = ParamSynchroSerializer(param, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        param = get_object_or_404(ParamSynchro, workspace=pk)
        param.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
