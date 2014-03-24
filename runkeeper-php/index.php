<?php
define('AUTHORIZATION_URL', 'https://runkeeper.com/apps/authorize');
define('TOKEN_URL', 'https://runkeeper.com/apps/token');
define('CLIENT_ID', 'a7f1c65a475342a48c6499dc167ce530');

$self_url = "http" . (!empty($_SERVER['HTTPS'])?"s":"") . "://".$_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI'];

if !(isset($_GET['code'])){
	header('Location: ' . AUTHORIZATION_URL . '?client_id=' . CLIENT_ID . '&response_type=code&redirect_uri=' . $self_url);
}
else {
	// convert token

}