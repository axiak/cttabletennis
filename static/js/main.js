	(function ($){
		$(document).ready(function () {
			$.crash();
		});
	})(jQuery);
	(function ($){
		var Dialog;
		$(document).ready(function() {
			Dialog = $("#division-dialog-modal");
			if (!Dialog.length) {
				return;
			}
			Dialog.dialog({
				height: 450,
				width: 500,
				modal: true,
				autoOpen: false
			});
			$("#singles a, #doubles a").bind("click", function (event) {
				var title ="Team Profile";
				if ($(this).parent().parent().attr("id") == "singles") {
					title = "Player Profile";
				}
				Dialog.dialog("option", "title", title);
				Dialog.html("<"+"p id='wait'><"+"img src='/media/img/loading.gif?1' border=0 /><"+"br />Loading...<"+"/p>");
				Dialog.dialog('open');
				Dialog.load(this.href);
				return false;
			});
		});
	})(jQuery);
	(function ($) {
		$(document).ready(function(){
			$("#players").accordion({
			        collapsible: true,
				active: false,
				animated: 'bounceslide',
				autoHeight: false,
				change: function (event, ui) {
					if (!ui.newContent.find("#wait").length) {
						return;
					}
					ui.newContent.load(ui.newContent.attr("data-url"));
				}
			});
			
		});
	})(jQuery);

