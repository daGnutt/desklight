NODEID = "68c63aa78e4a";

function fetchScenes()
{
	console.log("Fetching Scenes");
	var fetcher = new XMLHttpRequest();
	    fetcher.addEventListener("load", parseScenes );
	    fetcher.open( "GET", "/scenes?node=".concat( NODEID ) );
	    fetcher.send();
}

function parseScenes()
{
	console.log("Parsing Scenes");
	scenes = JSON.parse( this.responseText );
	console.log(scenes);

	selectedScene = null;
	document.getElementsByName("sceneselector").forEach(function(item) {
		if( item.checked ) { selectedScene = item.value; }
	});
	console.log( selectedScene );

	killAllChildren( document.getElementById( "scenelist" ) );

	for( var scene in scenes )
	{
		var newScene = document.createElement("li");
		var radio = document.createElement("input");
			radio.type = 'radio';
			radio.name = 'sceneselector';
			radio.value = scene;
			radio.addEventListener( "change", verifySendSceneButton );

		if( scene == selectedScene )
		{
			radio.checked = true;
		} else {
			radio.checked = false;
		}

		var editbutton = document.createElement("button");
			editbutton.addEventListener( "click", editScene );
			editbutton.appendChild( document.createTextNode("Edit") );

		var deletebutton = document.createElement("button");
			deletebutton.addEventListener( "click", verifyDeleteScene );
			deletebutton.appendChild( document.createTextNode( "Delete" ) );

		newScene.appendChild( radio );
		newScene.appendChild( document.createTextNode( scene ) );
		newScene.appendChild( editbutton );
		newScene.appendChild( deletebutton );
		document.getElementById("scenelist").appendChild( newScene );
	}
	verifySendSceneButton();
}

function editScene()
{
	console.log( this.parentElement.querySelector("input").value );
}

function verifyDeleteScene()
{
	console.log( this.parentElement.querySelector("input").value );
}

function verifySendSceneButton()
{
	selectedScene = null;
	document.getElementsByName("sceneselector").forEach(function(item) {
		if( item.checked ) { selectedScene = item.value; }
	});

	if( selectedScene == null )
	{
		document.getElementById("btnPushScene").disabled = true;
	} else {
		document.getElementById("btnPushScene").disabled = false;
	}
}

function sendScene()
{
	selectedScene = null;
	document.getElementsByName("sceneselector").forEach(function(item) {
		if( item.checked ) { selectedScene = item.value; }
	});

	if( selectedScene == null )
	{
		throw "No scene selected!";
	}

	var newScene = new XMLHttpRequest();
	newScene.open( "POST", "/setscene" );
	newScene.send( JSON.stringify( { node: NODEID, scene: selectedScene } ) );

	setTimeout( hidefeedback, 1000 );
	document.getElementById( "btnPushScene" ).disabled = true;
}
document.getElementById( "btnPushScene" ).addEventListener( "click", sendScene );

function sendBrightness()
{
	document.getElementById( "btnPushBrightness" ).disabled = true;
	brightness = parseInt(document.getElementById("rngBrightness").value);
	var newBrightness = new XMLHttpRequest();
		newBrightness.open( "POST", "/setbrightness" );
		newBrightness.send( JSON.stringify( { node: NODEID, brightness: brightness } ) );
	setTimeout( function() { document.getElementById( "btnPushBrightness" ).disabled = false;}, 1000 );
}
document.getElementById( "btnPushBrightness" ).addEventListener( "click", sendBrightness );

function hidefeedback()
{
	verifySendSceneButton();
}

function killAllChildren( domElement )
{
	while( domElement.firstChild )
	{
		domElement.removeChild( domElement.firstChild );
	}
}

setTimeout( fetchScenes, 0 );