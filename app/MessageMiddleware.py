from django.contrib import messages

class MessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for messagetype in ['successMessage', 'errorMessage']:
            if messagetype in request.session:
                if messagetype == 'successMessage':
                    level = messages.SUCCESS
                elif messagetype == 'errorMessage':
                    level = messages.ERROR
                else:
                    level = messages.INFO  # fallback
                messages.add_message(request, level, request.session[messagetype])
                del request.session[messagetype]
        response = self.get_response(request)
        return response