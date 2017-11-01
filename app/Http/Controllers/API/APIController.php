<?php

namespace App\Http\Controllers\API;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Http\Controllers\Controller;
use Predis\Client;

class APIController extends Controller
{
     public function send($sendId,$receiveId,$msg)
     {
         
         //DB::insert('insert into datalog (sender, receive, textdata) values (?, ?, ?)', [$sendId,$receiveId,$msg]);
         
         if($sendId > $receiveId){
             $first = $receiveId;
             $last = $sendId;
         }
         else{
             $first = $sendId;
             $last = $receiveId;
         }
         
         $client = new \Predis\Client();
         $client ->lpush("$first:$last", "$sendId:$msg");
         return response()->json(array(
                                       'result' => 'ok',
                                       'message' => 'message is sent',
                                       'data' => null
                                       ))->header('Access-Control-Allow-Origin', '*');;
     }
    
    public function get($sendId,$receiveId,$lastn)
    {
        
       // $message = DB::select('SELECT * FROM `datalog` where (sender =? and receive =?) or (sender =? and receive =?) order by id DESC limit ?', [$sendId,$receiveId,$receiveId,$sendId,$lastn]);
        
        if($sendId > $receiveId){
            $first = $receiveId;
            $last = $sendId;
        }
        else{
            $first = $sendId;
            $last = $receiveId;
        }
        
        $client = new \Predis\Client();
        $messages = $client ->lrange("$first:$last", 0,$lastn);
        
        $newMessages = array();
        foreach ($messages as $message) {
            $tmp = explode(":", $message);
            $newMessage = array(
                                'sender' => $tmp[0],
                                'receive' => $tmp[0] == $sendId ? $receiveId : $sendId,
                                'textdata' => $tmp[1],
                                );
            
            $newMessages[] = $newMessage;
        }
        return response()->json(array(
                                      'result' => 'ok',
                                      'message' => '',
                                      'data' => array_reverse($newMessages)
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

