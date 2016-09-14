$(document).ready(function () {
    console.log('coming here');
    // var address = prompt("enter your address");
    var mySocket = new WebSocket("ws://" + location.host + "/ws");
    // var mySocket = new WebSocket("ws://localhost:8080/ws");
    mySocket.onmessage = function (response) {
        console.log(response.type);
        $('#document').val(response.data);
    };
    $('#document').keyup(function (event) {
        console.log('coming here');
        var doc = $(this).val();
        mySocket.send(doc);
        event.preventDefault();
    });
})