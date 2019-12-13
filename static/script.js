$( document ).ready(function() {


  function createCanvas(parent, width, height) {
    var canvas = document.getElementById("inputCanvas");
    canvas.context = canvas.getContext('2d');
    return canvas;
  }

  function init(container, width, height, fillColor) {
    var canvas = createCanvas(container, width, height);
    var ctx = canvas.context;

    var imageObj = new Image();
    imageObj.onload = function(){
      ctx.drawImage(imageObj, 0, 0);
    };
    imageObj.src = '../static/images/previewWithPolygon.jpg';






    ctx.fillCircle = function(x, y, radius, fillColor) {
      this.fillStyle = fillColor;
      this.beginPath();
      this.moveTo(x, y);
      this.arc(x, y, radius, 0, Math.PI * 2, false);
      this.fill();
    };


    canvas.onmousemove = function(e) {
      if (!canvas.isDrawing) {
        return;
      }
      var x = e.pageX - this.offsetLeft;
      var y = e.pageY - this.offsetTop;
      var radius = 5;
      var fillColor = 'rgb(255,246,75)';
      ctx.fillCircle(x, y, radius, fillColor);
    };


    canvas.onmousedown = function(e) {
      canvas.isDrawing = true;
    };


    canvas.onmouseup = function(e) {
      canvas.isDrawing = false;
    };

    canvas.ondblclick  = function(e) {
      var x = e.pageX - this.offsetLeft;
      var y = e.pageY - this.offsetTop;
      var radius = 5;
      var fillColor = 'rgb(182,246,164)';
      ctx.fillCircle(x, y, radius, fillColor);

      getCursorPosition(this, e, x, y)

      $.ajax({
        url: "/ReadTableCoordinate",
        type: "get",
        success: function(response) {
          $("#place_for_table").html(response);
        },
      });


    };
  };



  var container = document.getElementById('canvas');
  init(container, 1200, 720, '#ddd');

  function clearCanvas() {
    var canvas = document.getElementById("inputCanvas");
    var ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var imageObj = new Image();
    imageObj.onload = function(){
      ctx.drawImage(imageObj, 0, 0);
    };
    imageObj.src = '../static/images/preview.jpg';
  }

  function getCursorPosition(canvas, event, x, y) {
    var outputData = [];
    outputData.push(x);
    outputData.push(y);

    $.post( "/saveRegion", {
      canvas_data: JSON.stringify(outputData)
    } , function(err, req, resp){
      window.location.href = "/preview";
    });


  }

  $( "#clearButton" ).click(function(){
    clearCanvas();
  });

  $( "#sendButton" ).click(function(){
    getData();
  });

  $("#ClearArea").click(function(){
    $.ajax({
      url: "/clearRegion",
      type: "get",
      success: function(response) {
        $("#place_for_table").html(response);
      },
    });
  });

  $("#inputCanvas").click(function(){
    $.ajax({
      url: "/ReadTableCoordinate",
      type: "get",
      success: function(response) {
        $("#place_for_table").html(response);
      },
    });
  });





  $("#StartStopSaveArea").click(function(){
    $.ajax({
      url: "/setRec",
      type: "get",
      success: function(response) {
        $("#place_for_rec").html(response);
      },
    });
  });






});