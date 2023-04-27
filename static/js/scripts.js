$("form[name=signup_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  $.ajax({
    url: "/user/signup",
    type: "POST",
    data: data,
    dataType: "application/json",
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
    url: "/newsource",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      // access_token = access_token + resp.access_token
      window.location.href = `/source?id=${resp.id}`;
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

$("form[name=bot_source_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  var bot_id = $form.attr("data-id");
  
    $.ajax({
    url: `/editbot/sources/add?id=${bot_id}`,
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      window.location.reload();
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

$("#source_submit_btn").click(function(e) {
  var $error = $("#source_submit_error")
  var $btn = $(this);
  var source_id = $btn.attr("data-id")
  // Perform AJAX call
  $.ajax({
    url: `/source/submit?id=${source_id}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      window.location.href = "/dashboard";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    },
    beforeSend: function () {
      $("#source_submit_btn_text").addClass('loader--hidden');
      $('#source_submit_btn_loader').removeClass('loader--hidden');
    },
    complete: function (response) {
      $('#source_submit_btn_loader').addClass('loader--hidden');
      $('#source_submit_btn_text').removeClass('loader--hidden');
    }
  });
  e.preventDefault();
});

$("#bot_regen_btn").click(function(e) {
  var $error = $("#bot_regen_error")
  var $btn = $(this);
  var bot_id = $btn.attr("data-id")
  // Perform AJAX call
  $.ajax({
    url: `/editbot/regen?id=${bot_id}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      window.location.href = `/chatbot?id=${bot_id}`;
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
    },
    beforeSend: function () {
      $("#bot_regen_btn_text").addClass('loader--hidden');
      $('#bot_regen_btn_loader').removeClass('loader--hidden');
    },
    complete: function (response) {
      $('#bot_regen_btn_loader').addClass('loader--hidden');
      $('#bot_regen_btn_text').removeClass('loader--hidden');
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
    url: `/editbot/delete?id=${bot_id}`, // URL of the API endpoint
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