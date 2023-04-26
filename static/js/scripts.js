$("form[name=signup_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  $.ajax({
    url: "/user/signup",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      // access_token = access_token + resp.access_token
      window.location.href = "/dashboard/";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    }
  });

  e.preventDefault();
});

$("form[name=signin_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  $.ajax({
    url: "/user/login",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      // access_token = access_token + resp.access_token
      window.location.href = "/dashboard/";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    }
  });

  e.preventDefault();
});

$("form[name=newbot_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  
    $.ajax({
    url: "/newbot",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      // access_token = access_token + resp.access_token
      window.location.href = "/dashboard/";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    },
    beforeSend: function () {
      $("#submit").addClass('loader--hidden');
      $('#loader').removeClass('loader--hidden');
    },
    complete: function (response) {
      $('#loader').addClass('loader--hidden');
      $('#submit').removeClass('loader--hidden');
    }
  });

  e.preventDefault();
});

$("#delete_btn").click(function(e) {
  var $error = $("#delete_err")
  var $btn = $(this);
  var bot_id = $btn.attr("data-id")
  // Perform AJAX call
  $.ajax({
    url: `/delbot?id=${bot_id}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      window.location.href = "/dashboard";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    },
  });
  e.preventDefault();
});

document.getElementById("script-box").addEventListener("click", function() {
  var copyText = document.getElementById("script-val");
  navigator.clipboard.writeText(copyText.innerText)
  
  var tooltip = document.getElementById("script-tooltip-text");
  tooltip.textContent = "Copied!";
  setTimeout(function() {
    tooltip.textContent = "Click to copy";
  }, 2000);
});
document.getElementById("iframe-box").addEventListener("click", function() {
  var copyText = document.getElementById("iframe-val");
  navigator.clipboard.writeText(copyText.innerText)
  
  var tooltip = document.getElementById("iframe-tooltip-text");
  tooltip.textContent = "Copied!";
  setTimeout(function() {
    tooltip.textContent = "Click to copy";
  }, 2000);
});