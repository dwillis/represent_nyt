(function(){
	this.popUp = function(url, name, params) {
		var win = window.open(url, name, params);
	};
}).call(NYTD.NYTINT);

// element mixins
NYTD.NYTINT.Mixins = {
	swap_classes: {
		elements: ['LI','A'],
		methods: {
			swapClasses: function(element, element2){
				element = $(element);
				element2 = $(element2);
				element.className = element2.className;
				element2.className = '';
				return element;
			}
		}
	},
	wrap_element: {
		elements: ['DIV','SPAN','UL','LI','A'],
		methods: {
			wrap: function(element, tagName) {
		    	element = $(element);
		    	var wrapper = document.createElement(tagName);
		    	element.parentNode.replaceChild(wrapper, element);
		    	wrapper.appendChild(element);
		    	return Element.extend(wrapper);
			}
		}
	}
};
for(var mixin in NYTD.NYTINT.Mixins)
	Element.addMethods(NYTD.NYTINT.Mixins[mixin].elements, NYTD.NYTINT.Mixins[mixin].methods);

NYTD.NYTINT.DefaultText = Class.create({
	initialize: function(element, default_text){
		this.element = $(element);
		this.default_text = default_text;
		
		if(this.element.value != this.default_text)
			this.element.style.color = "#333333";
				
		this.element.observe('click', this.focus.bindAsEventListener(this));
		this.element.observe('blur', this.blur.bindAsEventListener(this));
	},
	focus: function(){
		if(this.element.value == this.default_text) {
			this.element.value = "";
			this.element.style.color = "#333333";
		}
	},
	blur: function(){
		if(this.element.value == "") {
			this.element.value = this.default_text;
			this.element.style.color = "#cccccc";
		}
	}
});

(function(){
	this.query = function(shareType){
		var popUpUrl = window.location.href;
		switch(shareType){
			case "linkedin":
				NYTD.NYTINT.popUp('http://www.linkedin.com/shareArticle?mini=true' + '&url=' + encodeURIComponent(popUpUrl) + '&title=' + encodeURIComponent(document.title) + '&summary=' + encodeURIComponent(NYTD.NYTINT.pageConfig.description) + '&source=' + 'The New York Times', 'Linkedin', 'toolbar=0,status=0,height=550,width=700,scrollbars=yes,resizable=no');
				break;
    
			case "digg":
				NYTD.NYTINT.popUp('http://digg.com/remote-submit?phase=2&url=' + encodeURIComponent(popUpUrl) + '&title=' + encodeURIComponent(document.title) + '&bodytext=' + encodeURIComponent(NYTD.NYTINT.pageConfig.description), 'digg', 'toolbar=0,status=0,height=450,width=650,scrollbars=yes,resizable=yes');
				break;
    
			case "facebook":
				NYTD.NYTINT.popUp('http://www.facebook.com/sharer.php?u=' + encodeURIComponent(popUpUrl) + '&t=' + encodeURIComponent(document.title), 'sharer', 'toolbar=0,status=0,height=436,width=646,scrollbars=yes,resizable=yes');
				break;
    
			case "mixx":
				// recommended: 520x650
				NYTD.NYTINT.popUp('http://www.mixx.com/submit' + '?page_url=' + encodeURIComponent(popUpUrl), 'mixx', 'toolbar=0,status=0,height=550,width=700,scrollbars=yes,resizable=no');
				break;
    
			case "yahoobuzz":
				NYTD.NYTINT.popUp('http://buzz.yahoo.com/submit' + '?submitUrl=' + encodeURIComponent(popUpUrl) + '&submitHeadline=' + encodeURIComponent(document.title) + '&submitSummary=' + encodeURIComponent(NYTD.NYTINT.pageConfig.description) + '&submitCategory=politics&submitAssetType=article', 'yahoobuzz', 'scrollbars=no,resizable=yes,height=705,width=622');
				break;
    
			case "permalink":
				NYTD.NYTINT.popUp('http://mini.mixx.com/submit/story' + '?page_url=' + encodeURIComponent(popUpUrl) + passKey + otherParams, 'mixx', 'toolbar=0,status=0,height=550,width=700,scrollbars=yes,resizable=no');
				break;
		}		
	}
}).call(NYTD.NYTINT.Share);

// Hack to stop flickering of A tags with bg images - IE only
try { document.execCommand('BackgroundImageCache', false, true); } catch(e){ }

(function(){
	this.init = function(){
		if(window.attachEvent){			
			var suckerFishDropdowns = $$('#nytint-content ul.nytint-sf'); 
			for(var i = 0; (suckerFishDropdown = suckerFishDropdowns[i]); i++) this.attachHovers(suckerFishDropdown);
		}	
	},
	this.attachHovers = function(navRoot){
		for (i=0; i<navRoot.childNodes.length; i++){
			node = navRoot.childNodes[i];
			var pattern = /nytint\-sf/
    
			if (node.nodeName=="LI" && pattern.test(node.className) == true){
				node.onmouseover=function() {
					this.className+=" nytint-hover";
				};
				node.onmouseout=function() {
					this.className=this.className.replace(" nytint-hover", "");
				};
			}
		}			
	}
}).call(NYTD.NYTINT.Hover);

// 1.6ms to initialize, 97 function calls
NYTD.NYTINT.Tabs = Class.create({
	initialize: function(element) {
		this.element = $(element); // target ul
		
		this.options = Object.extend({
			selected: 		'nytint-selected'
		}, arguments[1] || {});
		
		this.private = {
			switchTo: function(element, parent){
				// hide current content
				$(this.current_tab.down().rel.substring(1)).hide();
				this.current_tab.removeClassName(this.options.selected);

				// show new content
				parent.addClassName(this.options.selected);
				$(element.rel.substring(1)).show();
				
				this.current_tab = this.element.select('.' + this.options.selected)[0];
			}.bind(this)
		};
		
		this.current_tab = this.element.select('.' + this.options.selected)[0]; // li
		
		if(!this.current_tab)
			throw "SelectorError: The default tab must have a class name of '" + this.options.selected + "'";
		this.element.observe('click', this.controller.bindAsEventListener(this));
		this.element.observe('tab:switch', this.radar.bindAsEventListener(this)); // handles custom event
	},
	controller: function(e) {
		var element = e.element(); // clicked anchor
		if(element.tagName != 'A')
			return false;

		Event.stop(e); // kill request
		
		this.private.switchTo(element, element.up());
	},
	radar: function(e){
		e = this.element.select('[rel=' + e.memo.tabName + ']')[0];
		this.private.switchTo(e, e.up());
	}
});

NYTD.NYTINT.App = Class.create({
	initialize: function(){
		this.options = Object.extend({
			templates: 		false,
			routing: 		false
		}, arguments[0] || {});
		
		this.state = {};
		
		if(this.options.templates)
			this.template_manager = new NYTD.NYTINT.TemplateManager();
		
		if(this.options.routing)
			this.map = new NYTD.NYTINT.Router(NYTD.NYTINT.routes || {});
		
		this.setApplicationState();
	},
	getTemplateManager: function(){
		return this.template_manager;
	},
	getRouter: function(){
		return this.router;
	},
	getApplicationState: function(){
		return this.state;
	},
	setApplicationState: function(){
		if(window.location.hash != '') {
			var state_pairs = window.location.hash.split('#')[1].split('&');
			for(var i=0, len=state_pairs.length; i<len; i++) {
				var pair = state_pairs[i].split('=');
				if(pair.length != 2) continue; // catch invalid hash
				this.state[pair[0]] = pair[1];
			}
		}
	}
});

NYTD.NYTINT.ActionAnchorSet = Class.create({
	initialize: function(element){
		this.element = $(element);
				
		this.options = Object.extend({
			anchorclass: 	''
		}, arguments[1] || {});
		
		this.actions = {};
		this.element.select('a' + this.options.anchorclass).each(function(anchor){
			this.actions[anchor.rel] = function(){};
		}.bind(this));
		
		this.element.observe('click',this.controller.bindAsEventListener(this));
	},
	controller: function(e){
		var element = e.element();
		Event.stop(e); // stop default action
		var action = element.rel;
		if(typeof this.actions[action] == 'function')
			this.actions[action](element); // pass element
	},
	setAction: function(action, fn){
		this.actions[action] = fn;
	}
});