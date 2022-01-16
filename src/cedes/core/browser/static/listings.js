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
