$(document).ready(function() {
    $('.votebuttons div').click(function() {
        if ($(this).hasClass('active')) {
            var vote = 'remove';
        } else {
            var vote = $(this).hasClass('upvote') ? 'up' : 'down';
        }

        const url = $(this).parent().attr('data-url');
        $.post(url, {'vote': vote}, vote_callback);
    });
});

function vote_callback(data) {
    wrapper = $('.votebuttons[data-vote-elem-pk=' + data.vote_elem_pk + ']');
    if (data.vote == 'up') {
        wrapper.children('.downvote').removeClass('active');
        wrapper.children('.upvote').addClass('active');
    } else if (data.vote == 'down') {
        wrapper.children('.upvote').removeClass('active');
        wrapper.children('.downvote').addClass('active');
    } else {
        wrapper.children('.upvote').removeClass('active');
        wrapper.children('.downvote').removeClass('active');
    }
    wrapper.children('.vote_sum').text(data.vote_sum);
    wrapper.attr('title', data.vote_count + ' Votes');
}
