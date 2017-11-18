<?php

namespace App\Http\Controllers\API;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Http\Controllers\Controller;
use Predis\Client;

class APIController extends Controller
{
    public $seperator = '$#^&^#$';
    public function send(Request $request,$sendId,$receiveId,$msg)
    {
         
        $token = $request->input('token');
        $id = $request->input('id');
        if(!$this->checkToken($token,$id)){
            return response()->json(['error' => 'Not authorized.'],403);
        }

        if($sendId > $receiveId){
            $first = $receiveId;
            $last = $sendId;
        }
        else{
            $first = $sendId;
            $last = $receiveId;
        }
        
        $client = new \Predis\Client();
        $ms = round(microtime(true)*1000);
        $messageid = $client->incr('messageid');
        $client ->lpush("$first". $this->seperator ."$last", "$sendId". $this->seperator ."$msg". $this->seperator ."$ms". $this->seperator ."$messageid");
        return response()->json(array(
                                    'result' => 'ok',
                                    'message' => 'message is sent',
                                    'data' => null
                                    ))->header('Access-Control-Allow-Origin', '*');
    }
    
    public function get(Request $request,$sendId,$receiveId,$lastn)
    {
        
        $token = $request->input('token');
        $id = $request->input('id');
        if(!$this->checkToken($token,$id)){
            return response()->json(['error' => 'Not authorized.'],403);
        }
        
        if($sendId > $receiveId){
            $first = $receiveId;
            $last = $sendId;
        }
        else{
            $first = $sendId;
            $last = $receiveId;
        }
        
        $client = new \Predis\Client();
        $messages = $client ->lrange("$first". $this->seperator ."$last", 0,$lastn);
        
        $newMessages = array();
        foreach ($messages as $message) {
            $tmp = explode($this->seperator, $message);
            $newMessage = array(
                                'sender' => $tmp[0],
                                'receive' => $tmp[0] == $sendId ? $receiveId : $sendId,
                                'textdata' => $tmp[1],
                                'time' => $tmp[2],
                                );
            
            $newMessages[] = $newMessage;
        }
        return response()->json(array(
                                      'result' => 'ok',
                                      'message' => '',
                                      'data' => array_reverse($newMessages)
                                      ))->header('Access-Control-Allow-Origin', '*');;
    }
    
    public function save2db(){
        $client = new \Predis\Client();
        $keys = $client->keys('*');
        
        foreach($keys as $key){
            if($key != "messageid"){
                $messages = $client->lrange($key,0,-1);
                
                $tmp = explode($this->seperator,$key);
                $maxid = DB::select('SELECT COALESCE(max(id),0) as maxid FROM `datalog` where (sender =? and receive =?) or (sender =? and receive =?) ', [$tmp[0],$tmp[1],$tmp[1],$tmp[0]]);
                
                $maxid = $maxid[0];
                $maxid = $maxid->maxid;
                
                foreach($messages as $message){
                        $parts = explode($this->seperator,$message);
                        $sender = $parts[0];
                        $message = $parts[1];
                        $time = $parts[2];
                        $messageid = $parts[3];
                    if($sender == $tmp[0]){
                        $receiver = $tmp[1];
                    }
                    else{
                        $receiver = $tmp[0];
                    }
                 
                    if($messageid > $maxid){
                        DB::insert('insert into datalog (id,sender, receive, textdata, time) values (?,?,?, ?, ?)', [$messageid,$sender,$receiver,$message,$time]);
                    }
                }
            }
            
        }
        
        return response("done");
    }
    
    private function checkToken($token,$id){
        return $token == '1234'&& $id == 'qwerty';
    }

    public function webhook(Request $request){
        $body = $request->getContent();
        error_log($body);

        $body = json_decode($body);
        
        if($body->object == 'page'){
            foreach($body->entry as $entry){
                $webhookEvent = $entry->messaging[0];
                $senderPsid = $webhookEvent->sender->id;

                if ($webhookEvent->message) {
                    $this->handleMessage($senderPsid, $webhookEvent->message);
                } else if ($webhookEvent->postback) {
                    $this->handlePostback($senderPsid, $webhookEvent->postback);
                }
            }

            return response()->json([
                'result' => 'EVENT_RECEIVED'
            ],200);
        }
        else{
            return response()->json([
                'result' => 'NOT_FOUND'
            ],404);
        }
    }

    private function handleMessage($senderPsid, $receivedMessage){
        if (isset($receivedMessage->text)) {
            $response = [
                "text" => "You sent the message: " . $receivedMessage->text . ". Now send me an image!"
            ];
        } else if (isset($receivedMessage->attachments)) {
            $attachmentUrl = $receivedMessage->attachments[0]->payload->url;
            $response = [
                "attachment" => [
                    "type" => "template",
                    "payload" => [
                        "template_type" => "generic",
                        "elements" => [[
                            "title" => "Is this the right picture?",
                            "subtitle" => "Tap a button to answer.",
                            "image_url" => $attachmentUrl,
                            "buttons" => [[
                                    "type" => "postback",
                                    "title" => "Yes!",
                                    "payload" => "yes",
                                ],
                                [
                                    "type" => "postback",
                                    "title" => "No!",
                                    "payload" => "no",
                                ]
                            ],
                        ]]
                    ]
                ]
            ];
        }
    
        $this->callSendAPI($senderPsid, $response);
    }

    private function handlePostback($senderPsid, $receivedPostback){
        $payload = $receivedPostback->payload;
    
        if ($payload === 'yes') {
            $response = [ "text" => "Thanks!" ];
        } else if ($payload === 'no') {
            $response = [ "text" => "Oops, try sending another image." ];
        }
        
        $this->callSendAPI($senderPsid, $response);
    }

    private function callSendAPI($senderPsid, $response) {

        $requestBody = [
            "recipient" => [
                "id" => $senderPsid
            ],
            "message" => $response
        ];

        $this->post("https://graph.facebook.com/v2.6/me/messages?access_token=EAAdGoMcQMJoBAHZCRur7Ur6J1HAQANBD5ZBSZCdvGE2bYKYMB0DwFHRI8oOWxl9RzbPP18ZA9NZCrOTWsZCeNiThA1i1YQcYcxkiVUDUmCGJwMufrkcfR7mXKkZB9HZB7gSzCuRU4Fkh5rXn8b7LRwkiY1QHQqsT7Fi8ZA3eYpHmAawZDZD",$requestBody);
    }

    private function post($url,$data){
        $body = json_encode($data);

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_HTTPHEADER, array("Content-Type: application/json"));
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        $result = curl_exec($ch);
    }

    public function webhookVerify(Request $request){
        $VERIFY_TOKEN = "150517ca445fbd6a705ca5b408e8c18b";
    
        $mode = $request->input('hub_mode');
        $token = $request->input('hub_verify_token');
        $challenge = $request->input('hub_challenge');

        if ($mode && $token) {
            if ($mode === 'subscribe' && $token === $VERIFY_TOKEN) {
                return response($challenge,200);
    
            } else {
                return response("ERROR",403);
            }
        }
        else{
            return response("ERROR",403);
        }
    }
}

