from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Exists, OuterRef
from .models import Movie, Review, MovieRequest, MovieRequestVote
from django.contrib.auth.decorators import login_required

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def movie_requests(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name and description:
            MovieRequest.objects.create(user=request.user, name=name, description=description)
        return redirect('movies.requests')

    template_data = {}
    template_data['title'] = 'Movie Requests'
    # Annotate with vote counts and whether current user has voted
    user_vote_subquery = MovieRequestVote.objects.filter(request=OuterRef('pk'), user=request.user)
    template_data['requests'] = (
        MovieRequest.objects
        .all()
        .annotate(vote_count=Count('votes'))
        .annotate(user_has_voted=Exists(user_vote_subquery))
        .order_by('-created_at')
    )
    return render(request, 'movies/requests.html', {'template_data': template_data})

@login_required
def delete_movie_request(request, id):
    movie_request = get_object_or_404(MovieRequest, id=id, user=request.user)
    movie_request.delete()
    return redirect('movies.requests')

@login_required
def vote_movie_request(request, id):
    if request.method != 'POST':
        return redirect('movies.requests')

    movie_request = get_object_or_404(MovieRequest, id=id)
    existing_vote = MovieRequestVote.objects.filter(request=movie_request, user=request.user)
    if existing_vote.exists():
        existing_vote.delete()
    else:
        MovieRequestVote.objects.create(request=movie_request, user=request.user)
    return redirect('movies.requests')