$(document).ready(function(){
	$( "#tabs" ).tabs();
	gifLoad();
	var socket = io.connect('/tweets');
    socket.on('connect', function() {
        console.log("socket connected");
    });
    socket.on('disconnect', function() {
        console.log("socket disconnected");
    });
    socket.on('tweet_text', function(data) {
	gifUnload();
        var obj = jQuery.parseJSON(data);
        var str = "<li class=\"tweet\">";
        str += "<span><img src=\""+obj.profile_image_url+"\"> "+obj.name+"</span>";
        str+= "<br/>"+obj.text+"</li>";
        $('.tweet_area ul').prepend(str);
            //addMessage(data);
    });

    $('#hashtag').dblclick(function(){
        $('.hashtag').removeAttr("readonly");
    });   
    $( 'form[name="frm1"]' ).submit(function( event ) {
	$(".hashtag").attr("readonly","readonly");
        var qstr = $(".hashtag").val();
        qstr=qstr.replace("#", ""); 
        qstr="/hashtag/%23"+qstr;
        $.get( qstr, function( data ) {
        });
        $(".hashtag").val("");
        event.preventDefault();
    }); 
});

function gifLoad() {
	$("#ExternalDiv").show();
	$("#InternalDiv").fadeIn("slow");

}
function gifUnload() {
	$("#InternalDiv").fadeOut("slow");
	$("#ExternalDiv").hide();
}
