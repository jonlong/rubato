/*

Last updated 2021-08-27
written by Sébastien Vaillancourt aka SebVé

sebve.com

*/

inlets  = 1;
outlets = 1;

var _loop_start  = 0;
var _loop_length = 1;
var _loop_start_time  = 0.
var _loop_length_time = 16;
var _offset = 0;
var _song_length = 0;
var _follow_state = 0;
var live_set;

var _cue_points        = [];
var _cue_points_sorted = [];
var _last_cue          = 1;

//live_set = new LiveAPI(follow_state(0), "live_set");

function path(_path)
{
	live_set = new LiveAPI(_path);
}

function cue_points(_cue_index, _cue_value)
{

	var _updated_cue = 0;
  	if (_cue_index == "clear")
	{
		_cue_points = [];
		return;
	}
	else
	{
		if (_cue_points[_cue_index] == undefined)
		{
			_cue_points[_cue_index] = _cue_value;
		}
		else
 		{
			_cue_points[_cue_index] = _cue_value;
			_updated_cue = 1;
		}
	}
	_cue_points_sorted = _cue_points.slice();
	_cue_points_sorted = _cue_points_sorted.sort(function comp(a, b){return a - b});
	if (_cue_points_sorted.length > 1) _last_cue = _cue_points_sorted.length - 1;
	if (_updated_cue)
	{
		_updated_cue = 0;
		output_data();
	}
}

function follow_state(_value)
{
	_follow_state = _value;
}

function follow_loop(_current_song_time)
{
	if (!_follow_state)	return; // exits immediately if not following
	if (_current_song_time > _cue_points_sorted[_last_cue])
	{
		nudge_loop(256);
		return; // exits if outside of the boundaries of song
	}
	for (var i = 0; i < _cue_points.length; i++) // probe each cue
	{
		if (_current_song_time >= _cue_points_sorted[i] && _current_song_time < _cue_points_sorted[i+1])
		{
			if (i == _loop_start) return;
			else
 			{
				nudge_loop(i - _loop_start); // move loop if passed a cue (only if it can)
				//if (_follow_state) outlet(0, "current_song_time " + _loop_start_time);
			}
		return;
		}
	}
}

function expand(_direction, _amount)
{
	if (_direction == "left") // if expanding/contracting to the left
	{
		if (_amount < 0)// contracting
		{
			if (_loop_length + _amount >= 1) // limit the contraction so that loop_length is not smaller than 1
			{
				_loop_length += _amount; // add the amount to the loop_length
				_loop_start -= _amount; // nudge
				update_loop_data();
				outlet(0, "loop_length " + _loop_length_time);
				outlet(0, "loop_start " + _loop_start_time);
				outlet(0, "loop_length_cues " + _loop_length);
			}
		}
		else // expanding
		{
			if (_amount > _loop_start) _amount = _loop_start; // limit the nudge by the amount of space left on the left
			_loop_start -= _amount; // nudge
			_loop_length += _amount; // add the amount to the loop_length
			update_loop_data();
			outlet(0, "loop_start " + _loop_start_time);
			outlet(0, "loop_length " + _loop_length_time);
			outlet(0, "loop_length_cues " + _loop_length);
		}
	}
	else if (_direction == "right") // if expanding/contracting to the right
	{
		if (_amount > 0) // expanding
		{
			var _room_after = _last_cue - (_loop_start + _loop_length);
			if (_amount > _room_after) _amount = _room_after; // limit the expansion to the room left after the loop
			_loop_length += _amount;
			update_loop_data();
			outlet(0, "loop_length " + _loop_length_time);
			outlet(0, "loop_length_cues " + _loop_length);
		}
		else // contracting
		{
			if (_loop_length + _amount >= 1) _loop_length += _amount; // restrict the contraction to a _loop_length of one
			update_loop_data();
			outlet(0, "loop_length " + _loop_length_time);
			outlet(0, "loop_length_cues " + _loop_length);
		}
	}
	else return;
}

function change_offset(_value)
{
	switch (_value)
	{
		case 0:
			_offset = -16.;
			break;
		case 1:
			_offset = -8.;
			break;
		case 2:
			_offset = -4.;
			break;
		case 3:
			_offset = -2.;
			break;
		case 4:
			_offset = -1.;
			break;
		case 5:
			_offset = 0.;
			break;
		case 6:
			_offset = 1.;
			break;
		case 7:
			_offset = 2.;
			break;
		case 8:
			_offset = 4.;
			break;
		case 9:
			_offset = 8.;
			break;
		case 10:
			_offset = 16.;
			break;
	}
	update_loop_data();
	outlet(0, "loop_length " + _loop_length_time);
	outlet(0, "loop_start "  + _loop_start_time);
}

function nudge_loop(_amount) // nudge the loop braces left or right
{
	var _room_after = _last_cue - (_loop_start + _loop_length);
	if (_amount >= 0)
	{
		_amount < _room_after ? _loop_start += _amount : _loop_start += _room_after; // nudge to the right unless at last cue
		update_loop_data();
		//live_set.set("loop_length", _loop_length_time);
		//live_set.set("loop_start", _loop_start_time);
		outlet(0, "loop_length " + _loop_length_time);
		outlet(0, "loop_start " + _loop_start_time);
	}
	else
	{
		-_amount < _loop_start ? _loop_start += _amount : _loop_start = 0; // nudge to the left until you hit the start
		update_loop_data();
		//live_set.set("loop_start", _loop_start_time);
		//live_set.set("loop_length", _loop_length_time);
		outlet(0, "loop_start " + _loop_start_time);
		outlet(0, "loop_length " + _loop_length_time);
	}
}

function loop_length(_value)
{
	if (_last_cue == undefined) _last_cue = 1;
	var _loop_length_max = _last_cue - _loop_start; // max loop size available
	if (_value < 1) _loop_length = 1;
	else if (_value >= _loop_length_max) _loop_length = _loop_length_max;
	else _loop_length = _value;
	outlet(0, "loop_length_cues " + _loop_length);
}

function update_loop_data()
{
	var _temp = _cue_points_sorted[_loop_start];
	if (_temp == undefined) _loop_start_time == 0.;
	else _loop_start_time = _temp + _offset;
	if (_loop_start_time < 0) _loop_start_time = 0;
	
	var _temp = _cue_points_sorted[_loop_start + _loop_length] - _cue_points_sorted[_loop_start];
	if (_temp == undefined) _loop_length_time == 16.;
	else _loop_length_time = _temp;
}


function output_data()
{
	update_loop_data();
/*	post("DUMPOUT loop_start_cues");  post(_loop_start);       post();
	post("DUMPOUT loop_length_cues"); post(_loop_length);      post();
	post("DUMPOUT loop_start_time");  post(_loop_start_time);  post();
	post("DUMPOUT loop_length_time"); post(_loop_length_time); post();
*/
	outlet(0, "loop_start "  + _loop_start_time);
	outlet(0, "loop_length " + _loop_length_time);
}

function dump()
{

	post("DUMPOUT loop_start_cues");  post(_loop_start);       post();
	post("DUMPOUT loop_length_cues"); post(_loop_length);      post();
	post("DUMPOUT loop_start_time");  post(_loop_start_time);  post();
	post("DUMPOUT loop_length_time"); post(_loop_length_time); post();
	post("DUMPOUT cue_points");       post(_cue_points_sorted); post();

	outlet(0, "loop_length " + _loop_length_time);
	outlet(0, "loop_start "  + _loop_start_time);
	outlet(0, "cue_points "  + _cue_points_sorted);	
}