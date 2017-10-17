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
         ));
     }
    
    public function test($message){
             return response()->json(array(
                 'result' => 'ok',
                 'message' => 'message is sent',
                 'data' => null
             ));
         }
    }

