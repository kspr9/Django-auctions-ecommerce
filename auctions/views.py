from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from django.forms import ModelForm
from django import forms

from .models import User, Listing, Bid, Comment, UsersWatchlist

from slugify import slugify


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
    widgets = {
          'comment': forms.Textarea(attrs={'rows':3, 'cols':35}),
        }


########################################################
###########   BASIC VIEWS   ############################
########################################################


def index(request):
    
    open_listings = Listing.objects.filter(closed=False).order_by("-publication_date").all()
    closed_listings = Listing.objects.filter(closed=True).order_by("-publication_date").all()
    
    return render(request, "auctions/index.html", {
        "listings": open_listings,
        "closed_listings": closed_listings,
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


########################################################
###########   AUCTION VIEWS   ##########################
########################################################


def categories(request):
    categories = Listing.LISTING_CATEGORY_CHOICES
    
    ## Creates a list with category name and associated slug 
    # to handle correct url path
    cats = []
    for cat in categories:
        #print(f'cat in categories: {cat}')
        cats.append((cat[1], slugify(cat[1])))
    #print(cats)
    return render(request, "auctions/categories.html", {"categories":cats})

def category(request, category_slug):
    categories_list = Listing.LISTING_CATEGORY_CHOICES
    
    ## Creates a list with listing_category key, name and slug
    categories_in_tuple = []
    for cat in categories_list:
        #print(f'cat in categories: {cat}')
        categories_in_tuple.append((cat[0], cat[1], slugify(cat[1])))
    #print(categories_in_tuple)
    
    ## Matches the slug with the key
    for cat_tuple in categories_in_tuple:
        if category_slug == cat_tuple[2]:
            found_cat = cat_tuple[0]
            sub_title = cat_tuple[1]
            break
    
    ## Selects all listings with found key
    listings_in_category = Listing.objects.filter(listing_category=found_cat).all()

    return render(request, "auctions/category.html", {
        "listings": listings_in_category,
        "category": sub_title,
    })



### Displays all users listing + there is a button to add a listing

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
    sold_listings = Listing.objects.filter(closed=True, seller=request.user.id).order_by("-publication_date").all()
    # get all listings where user is currently bidding
    # listing.bids.bidder == request.user
    bidding_on_listing = Listing.objects.filter(closed=False, bids__bidder=request.user.id).distinct()
    # get all listings won by user
    won = Listing.objects.filter(closed=True, winner=request.user.id).order_by("-publication_date").all()
    
    return render(request, "auctions/user_panel.html", {
        "selling": user_listings,
        "sold": sold_listings,
        "bidding": bidding_on_listing,
        "won": won,
    })


### Allows to add a new listing
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


### Defines what user can see on a listing detail page
#   Like add listing to a watchlist, bid and comment if user is logged in
#   If user is not logged in only basic listing info is displayed

def listing_page(request, listing_id):
    #print(f'listing_id coming from function arguments {listing_id}')
    listing_to_render = Listing.objects.get(pk=listing_id)

    #print(f'this is the request.user.id {request.user.id}')
    
    bid_form = BidForm()
    comment_form = CommentForm()
    

    ######  Helpers ########################################

    def check_on_watchlist():
        user = User.objects.get(id=request.user.id)
        ### handle on_watchlist variable
        watchlist_item = UsersWatchlist.objects.filter(
            watchlist_user = user,
            listing_in_watchlist = listing_id
            ).first()
            
        if watchlist_item is not None:
            on_watchlist = True
        else:
            on_watchlist = False
        
        return on_watchlist

    ######################################################
    ### Handles extra features if user is logged in
    ### returns listing page with bid form and on_watchlist if user is authenticated
    if request.user.is_authenticated:
        
        user = request.user
        #print(f'User of request.post is {user}')

        listing = listing_to_render
        #print(f'Listing that is going to be added to watchlist: {listing.id}')

        
        message = None
        

        ### add or delete listing from a watchlist
            # if the watchlist forms button click returned on_watchlist value=True
            # delete the item from the watchlist and set on_watchlist == False
        if "watchlist-form" in request.POST:
            
                # if listing removed from watchlist, 
                # delete the listing from watchlist 
            if "remove_from_watchlist" in request.POST:
                # delete the listing from the watchlist
                watchlist_listing = UsersWatchlist.objects.get(
                    watchlist_user = user,
                    listing_in_watchlist = listing
                )
                watchlist_listing.delete()
                
                # if the button returns on_watchlist value as False
                # create a new UserWatchlist instance
            if "add_to_watchlist" in request.POST:
                
                item_to_watchlist = UsersWatchlist(
                    watchlist_user=user,
                    listing_in_watchlist=listing
                )
                item_to_watchlist.save()


        ### closing and opening an auction (for the owner of a listing only)
            # checking for user == seller done on template side
            # close button not visible if user != seller
        if "close-form" in request.POST:
            
                # if listing is closed, 
                # change listing.closed to True 
            if "close_auction" in request.POST:
                # close the auction
                listing.closed = True
                if listing.bids.all().order_by('-bid_price').first() is not None:
                    highest_bid = highest_bid = listing.bids.all().order_by('-bid_price').first()
                    highest_bidder = highest_bid.bidder
                    listing.winner = highest_bidder
                    
                else:
                    highest_bidder = None
                listing.save()

                # if listing is opened
                # change listing.close to False
            if "open_auction" in request.POST:
                listing.closed = False
                if listing.winner is not None:
                    listing.winner = None
                listing.save()
        

        ### Handle commenting
            # save the comment form data into a Comment model
            # redirect back to listing page
        if "comment-form" in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = str(form.cleaned_data["comment"])
                
                new_comment = Comment()
                new_comment.comments_listing = listing
                new_comment.commenter = user
                new_comment.comment = comment
                new_comment.save()

        ### Perform the bidding (is user != seller)
            # save the form data into BidForm instance and 
            # redirect to listing_detail with listing_id
        if "bid-form" in request.POST:
            form = BidForm(request.POST)
            
            if form.is_valid():
                bid_price = float(form.cleaned_data["bid_price"])
                #listing_id = request.POST.get("listing_id")
                listing = listing_to_render
                user = user

                # don't allow for negative prices
                if bid_price <= 0 or bid_price <= listing.current_price:
                    #print(f'bid_price: {bid_price} <= listing.current_price: {listing.current_price}')
                    message = "Bid cannot be negative and bid has to be more than current price"

                # filter listing.bids and order by bid_price
                highest_bid = listing.bids.all().order_by('-bid_price').first()
                #print(f'highest bid: {highest_bid}')
                # save bid_price
                if highest_bid is None or bid_price > highest_bid.bid_price:
                    # save the bid to listing.bids
                    new_bid = Bid(bidder=user, bid_price=bid_price)
                    new_bid.save()
                    # add the new bid to bids of a listing
                    listing.bids.add(new_bid)
                    # update the current price of a listing
                    listing.current_price = bid_price
                    listing.save()
                    message = "You've successfully made the highest bid"

        ### handle highest bidder messages
        highest_bid = listing.bids.all().order_by('-bid_price').first()
        #print(f'highest bid: {highest_bid}')
        if highest_bid is not None:
            highest_bidder = highest_bid.bidder
            #print(f'highest bidder >> {highest_bidder}')
        else:
            highest_bidder = None
            #print(f'highest bidder >> {highest_bidder}')
        
        if highest_bidder is not None:
            if highest_bidder.id == request.user.id:
                bids_message = "Your bid is the highest bid"
            else:
                bids_message = "Highest bid made by " + highest_bidder.username
        else:
            bids_message = None


        ### handle winner announcement
        if listing.closed == True and request.user == listing.winner:
            bids_message = "You have won the auction!"


        ### handle comments on a listing page
        if Comment.objects.filter(comments_listing=listing) is not None:
            comments = Comment.objects.filter(comments_listing=listing)
        else:
            comments = None

        on_watchlist = check_on_watchlist() ### need user auth
        bids_count = listing_to_render.bids.count()
        #print(f' >>  Bids count: {bids_count}')

        context = {
            "listing": listing,
            "bid_form": bid_form,
            "on_watchlist": on_watchlist,
            "bids_count": bids_count,
            "bids_message": bids_message,
            "message": message,
            "comment_form": comment_form,
            "comments": comments,
            }
        
        return render(request, "auctions/listing_page.html", context)
        
    # count the bids made to a listing
    bids_count = listing_to_render.bids.count()
    bids_message = None

    return render(request, "auctions/listing_page.html", {
        "listing": listing_to_render,
        "bids_count": bids_count,
        "bids_message": bids_message,
    })


@login_required(login_url="auctions:login")
def watchlist(request):
    ### Then we handle the opening the watchlist page

    # getting the User models user id of the requests user
    watchlist_listings_ids = User.objects.get(id=request.user.id).watchlist.values_list("listing_in_watchlist", flat=True)
    #print(f'watchlist_listings_ids: {watchlist_listings_ids}')
    watchlist_items = []
    for id in watchlist_listings_ids:
        #print(f'IDs in watchlist_listings_ids (for loop): {id}')
        listing_to_watchlist = Listing.objects.get(id=id)
        watchlist_items.append(listing_to_watchlist)
        #print(f'watchlist_items after filtering Listing objects with the id: {watchlist_items}')
    return render(request, "auctions/watchlist.html", {
        "watchlist_items": watchlist_items,
    })


