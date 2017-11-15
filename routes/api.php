<?php

use Illuminate\Http\Request;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::middleware('auth:api')->get('/user', function (Request $request) {
    return $request->user();
});
    
Route::prefix('v1')->group(function() {

    Route::get('/save2db', 'API\APIController@save2db');
    Route::get('/send/{sendId}/{receiveId}/{msg}', 'API\APIController@send');
                           
    Route::get('/get/{sendId}/{receiveId}/{lastn}', 'API\APIController@get');
    
});
