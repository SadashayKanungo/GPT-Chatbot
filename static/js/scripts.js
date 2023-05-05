// Forms
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
      $error.addClass("error--success");
      $error.text(resp.msg).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
        $error.removeClass("error--success");
      }, 5000);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
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
      // access_token = access_token + resp.access_token
      window.location.href = "/dashboard/";
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    }
  });

  e.preventDefault();
});

$("form[name=forgot_password_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();

  $.ajax({
    url: "/user/forgotpassword",
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      $error.addClass("error--success");
      $error.text(resp.msg).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
        $error.removeClass("error--success");
      }, 5000);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    }
  });

  e.preventDefault();
});

$("form[name=password_reset_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  
    $.ajax({
    url: `/user/resetpassword`,
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      $error.addClass("error--success");
      $error.text(resp.msg).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
        $error.removeClass("error--success");
      }, 5000);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
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
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
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

$("form[name=bot_config_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  var bot_id = $form.attr("data-id");
  
    $.ajax({
    url: `/editbot/config?id=${bot_id}`,
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      document.location.reload(true);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
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
      // document.location.reload(true);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    },
    beforeSend: function () {
      $("#submit_add").addClass('loader--hidden');
      $('#loader_add').removeClass('loader--hidden');
    },
    complete: function (response) {
      $('#loader_add').addClass('loader--hidden');
      $('#submit_add').removeClass('loader--hidden');
    }
  });

  e.preventDefault();
});

$("form[name=bot_sitemap_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  var bot_id = $form.attr("data-id");
  
    $.ajax({
    url: `/editbot/sources/addsitemap?id=${bot_id}`,
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      console.log(resp);
      window.location.href = `/source?id=${resp.id}`;
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    },
    beforeSend: function () {
      $("#submit_sitemap").addClass('loader--hidden');
      $('#loader_sitemap').removeClass('loader--hidden');
    },
    complete: function (response) {
      $('#loader_sitemap').addClass('loader--hidden');
      $('#submit_sitemap').removeClass('loader--hidden');
    }
  });

  e.preventDefault();
});

$("form[name=source_add_form").submit(function(e) {

  var $form = $(this);
  var $error = $form.find(".error");
  var data = $form.serialize();
  var source_id = $form.attr("data-id");
  
    $.ajax({
    url: `/source/add?id=${source_id}`,
    type: "POST",
    data: data,
    dataType: "json",
    success: function(resp) {
      document.location.reload(true);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    }
  });

  e.preventDefault();
});

// Loader Buttons
$("#source_submit_btn").click(function(e) {
  var $error = $("#source_submit_error")
  var $btn = $(this);
  var source_id = $btn.attr("data-id");
  var ifBotId = $btn.attr("data-botId");
  console.log(ifBotId);
  if (ifBotId==="None"){
    var submit_url = `/source/submit?id=${source_id}`;
    var redirect_url = '/dashboard';
  } else{
    var submit_url = `/editbot/sources/addsitemap/submit?id=${ifBotId}&srcid=${source_id}`;
    var redirect_url = `/chatbot?id=${ifBotId}`;
  }
  
  // Perform AJAX call
  $.ajax({
    url: `${submit_url}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      window.location.href = redirect_url;
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
      window.location.href = `/dashboard`;
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
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

$("#bot_delete_btn").click(function(e) {
  var $error = $("#bot_delete_err")
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
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    },
  });
  e.preventDefault();
});

// Link Edit Buttons
$("button.source_action").click(function(e){
  var $btn = $(this);
  var id = $btn.attr('data-id');
  var index = $btn.attr('data-index');
  var action = $btn.attr('data-action');
  var $error = $(`#source_${action}_err`)
  // Perform AJAX call
  $.ajax({
    url: `/source/${action}?id=${id}&index=${index}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      document.location.reload(true);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    }
  });
  e.preventDefault();
});

$("button.bot_src_del").click(function(e){
  var $btn = $(this);
  var id = $btn.attr('data-id');
  var index = $btn.attr('data-index');
  var $error = $(`#bot_src_del_err`)
  // Perform AJAX call
  $.ajax({
    url: `/editbot/sources/drop?id=${id}&index=${index}`, // URL of the API endpoint
    type: "GET", // HTTP method
    success: function(data) {
      // Redirect to a new page on successful API call
      document.location.reload(true);
    },
    error: function(resp) {
      $error.text(resp.responseJSON.error).removeClass("error--hidden");
      setTimeout(()=>{
        $error.text("").addClass("error--hidden");
      }, 5000);
    }
  });
  e.preventDefault();
});

// Click to copy
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