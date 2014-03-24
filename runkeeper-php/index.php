<?php
require_once('settings.php'); // define CLIENT_SECRET and CLIENT_ID

define('AUTHORIZATION_URL', 'https://runkeeper.com/apps/authorize');
define('TOKENIZATION_URL', 'https://runkeeper.com/apps/token');

// send the user back here
$redirect_url = preg_replace("/\?.*$/i", "", "http" . (!empty($_SERVER['HTTPS'])?"s":"") . "://".$_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI']);

if (!(isset($_GET['code']))){
	$user = isset($_GET['user']) ? $_GET['user'] : time();
	header('Location: ' . AUTHORIZATION_URL . '?client_id=' . CLIENT_ID . '&response_type=code&redirect_uri=' . $redirect_url . '&state=' . $user);
}
else {
	$code = $_GET['code'];
	$user = isset($_GET['state']) ? $_GET['state'] : time();

	// convert code to token
	$ch = curl_init(TOKENIZATION_URL);
	curl_setopt($ch, CURLOPT_POST, true);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	
	$post_values = 'grant_type=authorization_code&code=' . $_GET['code'] . '&client_id=' . CLIENT_ID . '&client_secret=' . CLIENT_SECRET . '&redirect_uri=' . $redirect_url;
	curl_setopt($ch, CURLOPT_POSTFIELDS, $post_values); 
	
	$results = curl_exec($ch);

	file_put_contents(getcwd() . '/tokens/' . $user, $results);
	
	echo "<html><body>Thanks! You're all set.<br/><br/>&mdash;Tom</body></html>";
}