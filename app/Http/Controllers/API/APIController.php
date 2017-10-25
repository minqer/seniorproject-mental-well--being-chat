<?php

namespace App\Http\Controllers\API;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Http\Controllers\Controller;

class APIController extends Controller
{
     public function send($sendId,$receiveId,$msg)
     {
         
         DB::insert('insert into datalog (sender, receive, textdata) values (?, ?, ?)', [$sendId,$receiveId,$msg]);
         return response()->json(array(
                                       'result' => 'ok',
                                       'message' => 'message is sent',
                                       'data' => null
                                       ))->header('Access-Control-Allow-Origin', '*');;
     }
    
    public function get($sendId,$receiveId,$lastn)
    {
        
        $message = DB::select('SELECT * FROM `datalog` where (sender =? and receive =?) or (sender =? and receive =?) order by id DESC limit ?', [$sendId,$receiveId,$receiveId,$sendId,$lastn]);
        return response()->json(array(
                                      'result' => 'ok',
                                      'message' => '',
                                      'data' => array_reverse($message)
                                      ))->header('Access-Control-Allow-Origin', '*');;
    }

    
    public function test($message){
             return response()->json(array(
                 'result' => 'ok',
                 'message' => 'message is sent',
                 'data' => null
             ));
         }
    }

