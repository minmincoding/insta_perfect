// 바로실행 함수
$(function(){
  
    $('.serch_box > input').focus(function () {
        $('.serch_box > div').css('display', 'none');
    });
    $('.serch_box > input').blur(function () {
        $('.serch_box > div').css('display', 'block');
    });
    
    $(document).mouseup(function (e) {
        if ($(".modal_body").has(e.target).length === 0) {
            $(".modal_body").css('display', 'none');
            $('body').removeClass('hidden').off('scroll touchmove mousewheel');
        }
    });

    $('#photo_upload').change(function(){
        $('.modal_center').css('display', 'none');
        setImageFromFile(this, '#preview');
    });
    
    function setImageFromFile(input, expression) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function (e) {
                $(expression).attr('src', e.target.result);
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

})
//바로 실행 함수 종료

function feed_upload(){
    $('.modal_body').css('display', 'flex');
}

function photo_upload(){
    $('#photo_upload').click()
}


