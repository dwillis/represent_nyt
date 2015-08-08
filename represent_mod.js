NYTD.NYTINT.Represent = Class.create(NYTD.NYTINT.App, {
	initialize: function($super){
		$super();
		var instance = this;
		this.app = this.getApplicationState();
		this.tabs = 		$('nytint-tabs'); // get tabs element
		this.activity = 	$('nytint-activity-feed');
		this.floor = 		$('nytint-onthefloor');
		this.web = 			$('nytint-aroundtheweb');
		this.loader_icon = 	$('ajax-loader-icon');
		this.loaded = [];
		
		switch(this.app.r) { // get r value from hash
			case 'activityfeed':
				this.tabs.fire('tab:switch', { tabName: '#nytint-activity-feed' })
				this.loadContent('activityfeed');
				break;
			case 'onthefloor':
				this.tabs.fire('tab:switch', { tabName: '#nytint-onthefloor' })
				this.loadContent('onthefloor');
				break;
			case 'aroundtheweb':
				this.tabs.fire('tab:switch', { tabName: '#nytint-aroundtheweb' })
				this.loadContent('aroundtheweb');
				break;
			default:
				this.tabs.fire('tab:switch', { tabName: '#nytint-activity-feed' })
				this.loadContent('activityfeed');
				break;
		}
		
		var anchors = new NYTD.NYTINT.ActionAnchorSet(this.tabs);
		anchors.setAction('#nytint-activity-feed', function(element){
			window.location.hash = '#r=activityfeed';
			this.loadContent('activityfeed');
		}.bind(instance));
		anchors.setAction('#nytint-onthefloor', function(element){
			window.location.hash = '#r=onthefloor';
			this.loadContent('onthefloor');
		}.bind(instance));
		anchors.setAction('#nytint-aroundtheweb',function(element){
			window.location.hash = '#r=aroundtheweb';
			this.loadContent('aroundtheweb');
		}.bind(instance));
	},
	loadContent: function(feed){
		if(this.loaded.indexOf(feed) != -1) return;
		var instance = this;
		this.loader_icon.show();
		new Ajax.Request('/represent/' + NYTD.NYTINT.location + '/' + feed + '/', {
			method: 'get',
			onComplete: function(transport){
				switch(feed){
					case 'activityfeed':
						this.activity.insert(transport.responseText);
						break;
					case 'onthefloor':
						this.floor.insert(transport.responseText);
						break;
					case 'aroundtheweb':
						this.web.insert(transport.responseText);
						break;
					default:
						break;
				}
				this.loaded.push(feed);
				this.loader_icon.hide();
			}.bind(instance)
		});
	}
});
new NYTD.NYTINT.Represent();
