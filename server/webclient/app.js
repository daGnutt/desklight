NODEID = "68c63aa78e4a";

function setBrightnessToRecomended()
{
	document.getElementById( "rngBrightness" ).value = calculateRecommendeBrightness();
}

function calculateRecommendeBrightness()
{
	var selected_color = document.getElementById( "clrSelect" ).value;
	var rgb_value = hexToRgb( selected_color );
	var totalvalue = rgb_value.r + rgb_value.g + rgb_value.b;

	var recommended_brightness = ( 256 / totalvalue ) * 256;
	if( recommended_brightness > 255 ) {
		return 255;
	} else { return recommended_brightness }
}

function testForRecommendedBrightness()
{
	var selectedbrightness = parseInt(document.getElementById( "rngBrightness" ).value)
	if(selectedbrightness > calculateRecommendeBrightness() )
	{
		var change = confirm("You've tried to set higher than recomended brightness, revert?");
		if( change == true )
		{
			setBrightnessToRecomended();
		}
	}
}

function btnSetLight_Click()
{
	var hexcolor = document.getElementById( "clrSelect" ).value;
	var rgb_value = hexToRgb( hexcolor );
	var brightness = parseInt( document.getElementById( "rngBrightness" ).value );

	rgb_value.r = Math.round( ( rgb_value.r / 255 ) * brightness );
	rgb_value.g = Math.round( ( rgb_value.g / 255 ) * brightness );
	rgb_value.b = Math.round( ( rgb_value.b / 255 ) * brightness );

	var payload = rgb_value;
	payload.node = NODEID;
	payload.brightness = brightness;

	var sender = new XMLHttpRequest();
	    sender.open( "POST", "/setlight" );
	    sender.send( JSON.stringify( payload ) );
}

function hexToRgb(hex)
{
	var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function loadColor()
{
	var retriever = new XMLHttpRequest()
	retriever.addEventListener( "load", callback_loadColor );
	retriever.open( "GET", "/nodes" );
	retriever.send();
}

function callback_loadColor()
{
	if( this.status != 200 )
	{
		throw "Bad Form!";
	}
	nodes = JSON.parse(this.responseText);
	node = nodes[NODEID];
	document.getElementById( "rngBrightness" ).value = node.brightness;
	var factor = 255 / node.brightness;
	document.getElementById( "clrSelect" ).value = rgbToHex(node.pixels[0] * factor ,node.pixels[1] * factor ,node.pixels[2] * factor );
}

function componentToHex(c) {
    var hex = Math.round(c).toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

document.getElementById( "clrSelect" ).addEventListener( "change", setBrightnessToRecomended );
document.getElementById( "rngBrightness" ).addEventListener( "change", testForRecommendedBrightness );
document.getElementById( "btnSetLight" ).addEventListener( "click", btnSetLight_Click );
calculateRecommendeBrightness();
loadColor();