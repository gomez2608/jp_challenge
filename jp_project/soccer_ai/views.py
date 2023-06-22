from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
from http.client import HTTPSConnection
import json
from django.forms import *
from .analyzer import ResponseGenerator



# Create your views here.

oauth = OAuth()
oauth.register("auth0",
               client_id = settings.AUTH0_CLIENT_ID,
               client_secret = settings.AUTH0_CLIENT_SECRET,
               client_kwargs = {
                   "scope":"openid profile email"
               },
               server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",

               )


headers = {
    'x-rapidapi-host': "v1.volleyball.api-sports.io",
    'x-rapidapi-key': settings.API_KEY
    }



class LoginView(View):
    def get(self,request):
        print(request.build_absolute_uri(reverse("callback")))
        return oauth.auth0.authorize_redirect(
            request,request.build_absolute_uri(reverse("callback"))
        )


class CallbackView(View):
    def get(self,request):
        token = oauth.auth0.authorize_access_token(request)
        request.session["user"] = token
        return redirect(request.build_absolute_uri(reverse("home")))
    

class LogoutView(View):
    def get(self,request):
        request.session.clear()
        params = {
            "returnTo": request.build_absolute_uri(reverse("home")),
            "client_id": settings.AUTH0_CLIENT_ID
        }
        return redirect(f"https://{settings.AUTH0_DOMAIN}/v2/logout?{urlencode(params)}",quote_via=quote_plus)

class HomeView(View):
    
    def get(self, request):
        if request.session.get("user") == None:
            return render(request,"soccer_ai/login.html",{})
        else:
            conn = HTTPSConnection("v1.volleyball.api-sports.io")
            conn.request("GET", "/countries", headers=headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))
            countries_data = data.get("response")
            img_src = request.session.get("user").get("userinfo").get("picture")
            form = PromptForm()
            print(form.as_p())
            return render(request,"soccer_ai/home.html",{
                "session":request.session.get("user"),
                "pretty":json.dumps(request.session.get("user"), indent=4),
                "img_src":img_src,
                "form":form.as_p(),
                "countries":countries_data

            })
        

class PromptForm(Form):
    input_prompt = CharField(widget=Textarea)


class AnalizerView(View):
    def get(self,request):
        prompt = request.GET.get("prompt","")
        if prompt != "":
            response_gen = ResponseGenerator("global_db.csv")
            resp = response_gen.get_answer(prompt)
        else:
            resp = "There is no suministred prompt"
        return render(request,"ans_view.html",{"resp":resp})