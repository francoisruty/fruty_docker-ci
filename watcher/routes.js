var express = require('express');
var router = express.Router();
var axios = require('axios');
var prependFile = require('prepend-file');

const { execSync } = require('child_process');


var log = function(txt) {
  var timestamp = new Date().toISOString();
  prependFile('/logs/main.txt', timestamp + ' - ' + txt + "\n", function (err) {
    if (err) {
      console.log("Error with prepend");
    }
  });
};
global.log = log;


// application -------------------------------------------------------------
router.get('/', function (req, res) {

});


//NOTE: we want file change events to know which commit is the cause of the file change.
//Since the function that pulls the repo and the one that processes file changes are totally
//independent, this is not trivial.
//We use a global variable to store head commit, and since execSync is synchronous,
//I think the likelihood that git pull and file change detection proceed synchronously is extremely
//high, in the context of concurrent api requests. We'll see down the road how it plays out.

router.post('/hook', function (req, res) {
  var repo = req.body.repository.name;
  console.log("hook - repo: " + repo + " - branch: " + req.body.ref);
  log("hook - repo: " + repo + " - branch: " + req.body.ref);

  //We monitor only "master" branch
  if (req.body.ref == 'refs/heads/master') {

    var headCommit = req.body.head_commit.id;

    //we refresh the relevant repo
    var result = execSync('cd /git_data/' + repo + ' \n git checkout master \n git pull origin master');
    result = result.toString();
    log('Git pull OK');
    axios.post('http://flower:5555/api/task/async-apply/build', {
      args: [repo,headCommit]
    })
    .then(function (response) {
      console.log("SUCCESS");
      log("Build POST succeeded")
      console.log(response);
    })
    .catch(function (error) {
      console.log("ERROR");
      log("Build POST failed")
      console.log(error);
    });
  }

  res.status(200)
  .json({
    status: 'success',
    data: '',
    message: 'hook successful'
  });
});


module.exports = router;
