$(document).ready(function () {
    console.log('coming here');
    var mySocket = new WebSocket("ws://" + location.host + "/ws");
    mySocket.onmessage = function (response) {
        $('#document').val(response.data);
    };
    $('#document').keyup(function (event) {
        var doc = $(this).val();
        mySocket.send(doc);
        event.preventDefault();
    });
})