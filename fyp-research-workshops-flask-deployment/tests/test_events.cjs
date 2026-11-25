const { JSDOM } = require("jsdom");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { execFileSync } = require("node:child_process");
const html = execFileSync("python", ["-c", "from app import app; print(app.test_client().get('/').get_data(as_text=True))"], {
  encoding: "utf8", env: {...process.env, GA4_MEASUREMENT_ID: "G-C05T96EVF8", DATABASE_URL: "sqlite://"}
});
async function run() {
  function initialize(url) {
  const {window: w} = new JSDOM(html, {runScripts: "outside-only", url, referrer: "https://source.example/private?email=test"});

  for (const script of w.document.querySelectorAll("script:not([src])")) w.eval(script.textContent);
  return w;
  }
  for (const suffix of ["?email=private", "?utm_source=Alice", "?utm_source=wechat&utm_source=email",
                        "?utm_source=wechat&student_id=123", "?utm_campaign=test%40example.com",
                        "?constructor=x", "#private"]) {
    const blocked = initialize("https://site.example/" + suffix);
    assert.equal(blocked.gtag, undefined);
    assert.equal(blocked.document.querySelector("script[src*=googletagmanager]"), null);
    blocked.close();
  }
  const campaign = "?utm_source=wechat&utm_medium=social&utm_campaign=phase1a_baseline";
  const w = initialize("https://site.example/" + campaign + "#workshops");
  const q = selector => w.document.querySelector(selector);
  assert.equal(w.document.querySelectorAll("script[src*=googletagmanager]").length, 1);
  const direct = initialize("https://site.example/");
  assert.equal(direct.dataLayer[1][2].page_location, "https://site.example/");
  direct.close();
  const config = w.dataLayer[1][2];
  assert.equal(config.page_location, "https://site.example/" + campaign);
  assert.equal(config.page_referrer, "https://source.example/");
  w.eval(fs.readFileSync("static/js/script.js", "utf8"));
  const events = () => JSON.parse(JSON.stringify(w.dataLayer.filter(x => x[0] === "event").map(x => Array.from(x).slice(1))));
  const fire = (selector, type) => q(selector).dispatchEvent(new w.Event(type, {bubbles:true,cancelable:true}));
  const filter = q('[data-filter="planning"]');
  filter.click(); filter.click();
  q("dialog").showModal = () => {};
  q(".details-button").click();
  q("dialog").close = () => {};
  q("#register").scrollIntoView = () => {};
  q(".dialog-register").click();
  const expected = [["workshop_filter_selected",{workshop_category:"planning"}],["workshop_details_opened",{workshop_id:"question"}]];
  assert.deepEqual(events(),expected);
  fire("form","submit");
  assert.deepEqual(events(),expected);
  let status = 422;
  let posts = 0;
  w.fetch = async (_, options) => {
    posts++;
    return {status, ok:status===201, json:async () => ({requestType:JSON.parse(options.body).requestType,reference:"FYP-PRIVATE"})};
  };
  const settle = () => new Promise(resolve => setImmediate(resolve));
  for (const [label, value] of [["Register interest","register_interest"],["Make an enquiry","make_an_enquiry"]]) {
    q("#full-name").value="Demo Person"; q("#email").value="demo@example.com"; q("#message").value="private message";
    q("#workshop-select").value="question"; q("#demo-consent").checked=true; q('input[value="'+label+'"]').checked=true;
    fire("#email","input"); fire("#email","change");
    expected.push(["interest_form_started"]);
    status=422; fire("form","submit"); await settle(); assert.deepEqual(events(),expected);
    status=201; const before=posts; fire("form","submit"); fire("form","submit");
    assert.deepEqual(events(),expected); await settle(); assert.equal(posts,before+1);
    expected.push(["interest_form_success",{request_type:value}]); assert.deepEqual(events(),expected);
  }
  w.close(); console.log("PASS: config privacy, filter deduplication, dialog/preselection, starts, validation, 422, delayed 201, double submit, both request types and exact event payloads.");
}
run().catch(e=>{console.error(e);process.exitCode=1;});
