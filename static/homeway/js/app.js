$(document).ready(function(){

	//处理框架事件
	var myApp = new Framework7({
	  modalTitle: '点歌台小助手',
	  init: false //Disable App's automatica initialization
	});
	var $$ = Dom7;
	var mainView = myApp.addView('#main-music', {
    	// dynamicNavbar: true,
    	// attachEvents:true
	});
	var view2 = myApp.addView('#view-2', {
    	dynamicNavbar: true,
    	attachEvents:true,
    	handleTouchEnd: function(e){
    		alert('end');
    	}
	});
	var view3 = myApp.addView('#view-3');
	var view4 = myApp.addView('#view-4');

	myApp.onPageInit('main-page', function (page) {
        mainView.router.load({
            url: 'play-list.html'
        });
    });

	//And now we initialize app
	myApp.init();
	// myApp.modal({title: '点歌台小助手'});
	//console.log(view2);
	
	$('#search').click( function (e){
		var data = {
			'key': $('#key').val(),
		}
		$.post('/ajaxSearch', data, function (res){
			if(res){
				var result = res['songs'];
				var html ='<li><div class="item-content"><div class="item-inner"><div class="item-title">歌曲</div><div class="item-after">歌手</div></div></div></li>';
				for( var i=0; i<result.length; i++){
					console.log( result[i]['id'] );
					html += '<li><a href="/song.html?sid='+result[i]['id']+'" class="item-link"><div class="item-content"><!--img src="'+result[i]['blurPicUrl']+'"--><div class="item-inner"><div class="item-title">'+result[i]['name']+'</div><div class="item-after">'+result[i]['artists'][0]['name']+'</div></div></div></a></li>';
					$('#list-album').html(html).slideDown( {duration: 1000});
				}
			}else{

			}
		},'json');
	});

	var load_new_albums = function(){
		$.ajax({
			url : '/ajaxNewAlbums',
			method : 'POST',
			dataType: 'json',
			data : {'offset': 0, 'limit':10 },
			beforeSend: function( xhr ) {
    			//菊花转起来
    		},
    		success: function( res ){
    			//console.log(res);
    			var result = res;
				var html ='<li><div class="item-content"><div class="item-inner"><div class="item-title">歌曲</div><div class="item-after">歌手</div></div></div></li>';
				for( var i=0; i<result.length; i++){
					//console.log( result[i]['id'] );
					html += '<li><a href="/album.html?aid='+result[i]['id']+'" class="item-link"><div class="item-content"><div class="item-inner"><div class="item-title">'+result[i]['name']+'</div><div class="item-after">'+result[i]['artists'][0]['name']+'</div></div></div></a></li>';
					$('#list-album').html(html).slideDown( {duration: 10, easing: 'easeOutQubic'});
				}
    		},
		});
	};

	var load_hot_song = function(){
		$.ajax({
			url : '/ajaxHotSong',
			method : 'POST',
			dataType: 'json',
			data : {'offset': 0, 'limit':10 },
			beforeSend: function( xhr ) {
    			//菊花转起来
    		},
    		success: function( res ){
    			//console.log(res);
    			var result = res;
				var html ='<li><div class="item-content"><div class="item-inner"><div class="item-title">歌曲</div><div class="item-after">歌手</div></div></div></li>';
				for( var i=0; i<result.length; i++){
					//console.log( result[i]['id'] );
					html += '<li><a href="/song.html?sid='+result[i]['id']+'" class="item-link"><div class="item-content"><div class="item-inner"><div class="item-title">'+result[i]['name']+'</div><div class="item-after">'+result[i]['artists'][0]['name']+'</div></div></div></a></li>';
					$('#list-hot-song').html(html).slideDown( {duration: 10, easing: 'easeOutQubic'});
				}
    		},
		});
	};

	$('#menu-tab-search').click(function (e){
		load_new_albums();
		load_hot_song();
	});

	// 播放
	$(document).on('click', '#player', function (e){
		var t = $(this);
		var req = { 
            url: t.parent().attr('data-url'),
            sid : t.parent().attr('data-id'),
        }
        $.ajax({
            url : '/ajaxPlayMusic',
            method : 'POST',
            dataType: 'json',
            data : req,
            beforeSend: function( xhr ) {
                //菊花转起来
                $("#player").html('歌曲下载中...');
            },
            success: function( res ){
                //显示播放
                $("#player").html('播放中...');
            },
        });
	});

	// 点歌
	$(document).on('click', '#addorder', function (e) {
		var p = $(this).parent();
		var req = {
			name: p.attr('data-name'),
            url: p.attr('data-url'),
            sid : p.attr('data-id'),
			duration: p.attr('data-duration'),
			artists: p.attr('data-artists'),
			album_pic: p.attr('data-album-pic'),
			album_name: p.attr('data-album-name'),
        }
        $.ajax({
            url : '/ajaxOrderMusic',
            method : 'POST',
            dataType: 'json',
            data : req,
            beforeSend: function( xhr ) {
                $("#addorder").attr("disabled",true);
            },
            success: function( res ){
            	if (res.result) {
            		myApp.alert('点歌成功');
            	}else{
            		myApp.alert('点歌失败：' + res.info);
            	}
                
            },
        });
	});

	// 开始播放
	$(document).on('click', '#start-play', function (e) {
        $.post('/ajaxPlayMusic', {sid:'', url:''}, function (res){
            if (!res.result) {
            	myApp.alert('播放出错：' + res.info)
            }
        },'json');
	});

	// 暂停播放
	$(document).on('click', '#pause-play', function (e) {
        $.post('/ajaxPauseMusic', {}, function (res){
            if (!res.result) {
            	myApp.alert('播放出错：' + res.info)
            }
        },'json');
	});

	// 调节音量
	$(document).on('click', '.set-volume', function (e) {
		var value = $(this).val();
        $.post('/ajaxSetVolume', {'value': value}, function (e){
            //alert('set volume success!!');
        },'json');
	});

	$(document).on('click', '.album_panel', function (e) {
        $.ajax({
            url : '/ajaxNewAlbums',
            method : 'POST',
            dataType: 'json',
            data : {'offset': 0, 'limit':10 },
            beforeSend: function( xhr ) {
                //菊花转起来
            },
            success: function( res ){
                //console.log(res);
                var result = res;
                var html ='<li><div class="item-content"><div class="item-inner"><div class="item-title">歌曲</div><div class="item-after">歌手</div></div></div></li>';
                for( var i=0; i<result.length; i++){
                    //console.log( result[i]['id'] );
                    html += '<li><a href="/album.html?aid='+result[i]['id']+'" class="item-link"><div class="item-content"><div class="item-inner"><div class="item-title">'+result[i]['name']+'</div><div class="item-after">'+result[i]['artists'][0]['name']+'</div></div></div></a></li>';
                    $('#list-album').html(html).slideDown( {duration: 1000, easing: 'easeOutQubic'});
                }
            },
        });
    });



});






















