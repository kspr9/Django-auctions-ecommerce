from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from django.forms import ModelForm

from .models import User, Listing, Bid, Comment


########################################################
###########   FORMS   ##################################
########################################################

class CreateListingsForm(ModelForm):
  class Meta:
    model = Listing
    fields = [
        'title', 
        'current_price', 
        'description', 
        'listing_category', 
        'image_url',
    ]


class BidForm(ModelForm):
  class Meta:
    model = Bid
    fields = ["bid_price"]


class CommentForm(ModelForm):
  class Meta:
    model = Comment
    fields = ["comment"]


########################################################
###########   BASIC VIEWS   ############################
########################################################


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.order_by("-publication_date").all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url="auctions:login")
def user_listings(request):
    """User Listings view: shows all listings that user:
        * is currently selling
        * sold
        * is currently bidding
        * won
    """

    # get all listings that user has created
    user_listings = Listing.objects.filter(closed=False, seller=request.user.id).order_by("-publication_date").all()

    # get all listings sold by user
    sold = []
    # get all listings where user is currently bidding
    bidding = []
    # get all listings won by user
    won = []
    
    return render(request, "auctions/user_listings.html", {
        "selling": user_listings,
        "sold": sold,
        "bidding": bidding,
        "won": won,
    })
