from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from django.forms import ModelForm

from .models import User, Listing, Bid, Comment, UsersWatchlist


########################################################
###########   FORMS   ##################################
########################################################

class ListingForm(ModelForm):
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


@login_required(login_url="auctions:login")
def add_listing(request):
    if request.method == "GET":
        return render(request, "auctions/add_listing.html", {
            "form": ListingForm(),
        })
    
    if request.method == "POST":
        form = ListingForm(request.POST)
        seller = User.objects.get(pk=request.user.id)
        if form.is_valid():
            # Get all data from the form and assign into variables

            listing_title = form.cleaned_data.get("title") 
            starting_price = form.cleaned_data.get('current_price')
            listing_description = form.cleaned_data.get('description')
            listing_category = form.cleaned_data.get('listing_category')
            listing_image = form.cleaned_data.get('image_url')

            # saving the form data, but not committing yet to add the seller after
            listing = form.save(commit=False)
            listing.seller = seller
            # final save
            listing.save()
            return HttpResponseRedirect(reverse("auctions:user_listings"))
        else:
            return render(request, "auctions/add_listing.html", {
                "form": form,
                "message": "Check your input data!",
            })

def listing_page(request, listing_id):
    listing_to_render = Listing.objects.get(pk=listing_id)
    return render(request, "auctions/listing_detail.html", {
        "listing": listing_to_render,
    })


@login_required(login_url="auctions:login")
def watchlist(request):
    #### first we implement the add/remove to/from watchlist
    
    # since this route is called only after button click, we will have a request.POST data
    if request.method == "POST":
        # getting the listing_id from the request.POST data
        # this name is given on the listing detail page within the add/remove watchlist form
        listing_id = request.POST.get("listing_id")

        listing = Listing.objects.get(pk=listing_id)
        user = User.objects.get(id=request.user.id)

        # add or delete listing from a watchlist
        # if the watchlist forms button click returned on_watchlist value=True
        # delete the item from the watchlist and set on_watchlist == False
        if request.POST.get("on_watchlist") == "True":
            # delete the listing from the watchlist
            watchlist_listing = UsersWatchlist.objects.filter(
                watchlist_user = user,
                listing_in_watchlist = listing
            )
            watchlist_listing.delete()
        # if the button returns on_watchlist value as False
        # create a new UserWatchlist instance
        else:
            item_to_watchlist = UsersWatchlist(
                watchlist_user = user,
                listing_in_watchlist = listing
            )
            item_to_watchlist.save()
        return redirect("auctions:listing_detail", listing_id)
    
    ### Then we handle the opening the watchlist page

    # getting the User models user id of the requests user
    watchlist_listings_ids = User.objects.get(id=request.user.id).watchlist.values_list("listing_in_watchlist")
    watchlist_items = Listing.objects.filter(id_in=watchlist_listings_ids, closed=False)

    return render(request, "auctions/watchlist.html", {
        "watchlist_items": watchlist_items
    })