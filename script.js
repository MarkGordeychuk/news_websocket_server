$(function() {
  var ul = $('#list > ul');

  var newsList = [];
  var newsListeners = new Set();
  function addNews(news) {
    newsList.push(news);
    newsListeners.forEach(function (listener) {
      listener(news);
    });
  }

  newsListeners.add(
    function (news) {
      ul.append($("<li></li>").text(news));
    }
  );

  var form = $('#send-message > form').submit(function (e) {
    e.preventDefault();
    $.post("news", form.serialize());
  });

  $('#check-con').click(function () {
    $.get("check", function (data) {
      alert(data.connection ? "Соединение установлено" : "Соединение не установлено");
    })
  });

  $('#con').click(connect);

  var conn = null;

  function connect() {
    disconnect();
    var wsUri = (window.location.protocol==='https:'&&'wss://'||'ws://')+window.location.host;
    conn = new WebSocket(wsUri);
    console.log('Connecting...');
    conn.onopen = function() {
      console.log('Connected.');
    };
    conn.onmessage = function(e) {
      console.log('Received: ' + e.data);
      addNews(JSON.parse(e.data).data);
    };
    conn.onclose = function() {
      console.log('Disconnected.');
      conn = null;
    };
  }

  function disconnect() {
    if (conn != null) {
      console.log('Disconnecting...');
      conn.close();
      conn = null;
    }
  }

  connect();
});