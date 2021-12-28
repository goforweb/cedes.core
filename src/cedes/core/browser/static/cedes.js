// used in pressbanking_import to automatically select the corresponding
// box while selecting a group value from 0 to 15
selectCorrespondingBox = function(inputValue, current){
if (current.value=="0") {
  $("input[value="+inputValue+"]")[0].checked=false;
  }
  else
  {
  $("input[value="+inputValue+"]")[0].checked=true;
  }
};

// function that load prices (total and real) of a dossierstructure in an async
// way to speed up dossier_view
// we hide the spinner as this is called "onload"
function showRealPrice(UID, baseUrl) {
  var spinner = $('#ajax-spinner').hide();
  $(document).ajaxStart(function() { spinner.hide(); });
  $(document).ajaxStop(function() { spinner.hide(); });
  jq.ajax({
    url: baseUrl + "/@@ds_price",
    dataType: 'html',
    data: {UID:UID},
    cache: false,
    success: function(data) {
      var selector = '#marker_ds_price_' + UID;
      var $span = jq(selector);
      $span.html(data);
      },
    error: function(jqXHR, textStatus, errorThrown) {
      /*console.log(textStatus);*/
      }
    });
}

/* used to show/hide details */
function toggleDoc(tag, toggle_parent_active=true) {
  elem = $(tag).next('div')
  elem.slideToggle(200);
  if (toggle_parent_active) {
    elem.prev()[0].classList.toggle("active");
  }
}

$(document).ready(function () {
  Faceted.Options.FADE_SPEED=0;
  Faceted.Options.SHOW_SPINNER=false;
})

function resetFaceted() {
  $.each(Faceted.Query,
    function(k, v){
         delete Faceted.Query[k];
       });
  Faceted.Form.do_query();
}
