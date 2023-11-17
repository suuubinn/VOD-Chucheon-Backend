from django.shortcuts import render,redirect


# Create your views here.
def landing(request):
    islogged = request.user.is_authenticated
    if islogged:
        return redirect('/main')
    if request.method == "GET":
        return render(request, 'landing.html')


def main(request):
    if request.method == "GET":
        return render(request, 'main/main.html')