(function () {
  var input = document.getElementById("q");
  var shelves = document.getElementById("shelves");
  var results = document.getElementById("results");
  var more = document.getElementById("more");
  var empty = document.getElementById("empty");
  var count = document.getElementById("count");
  var data = window.WTL_INDEX || [];
  var maxHits = 24;

  function esc(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function initials(title) {
    var parts = String(title || "").replace(/&/g, " ").split(/\s+/);
    var letters = "";
    for (var i = 0; i < parts.length && letters.length < 2; i++) {
      if (parts[i] && /[A-Za-z0-9]/.test(parts[i].charAt(0))) {
        letters += parts[i].charAt(0).toUpperCase();
      }
    }
    return letters || "W";
  }

  function hue(slug) {
    var n = 0;
    for (var i = 0; i < slug.length; i++) n += slug.charCodeAt(i);
    return n % 360;
  }

  function card(row) {
    var title = row[0];
    var slug = row[1];
    var cat = row[2];
    var pub = row[3];
    return (
      '<a class="card" href="podcasts/' + esc(slug) + '/">' +
        '<div class="sleeve" style="--hue:' + hue(slug) + '">' +
          '<span class="initials" aria-hidden="true">' + esc(initials(title)) + "</span>" +
        "</div>" +
        '<div class="card-body">' +
          '<span class="cat">' + esc(cat) + "</span>" +
          "<h2>" + esc(title) + "</h2>" +
          '<p class="host">' + esc(pub) + "</p>" +
        "</div>" +
      "</a>"
    );
  }

  function apply() {
    var q = (input && input.value ? input.value : "").trim().toLowerCase();
    if (!q) {
      if (shelves) shelves.hidden = false;
      if (results) {
        results.hidden = true;
        results.innerHTML = "";
      }
      if (more) more.hidden = true;
      if (empty) empty.classList.remove("show");
      if (count) count.textContent = String(data.length);
      return;
    }
    var hits = [];
    var total = 0;
    for (var i = 0; i < data.length; i++) {
      var row = data[i];
      var hay = (row[0] + " " + row[2] + " " + row[3]).toLowerCase();
      if (hay.indexOf(q) === -1) continue;
      total += 1;
      if (hits.length < maxHits) hits.push(row);
    }
    if (shelves) shelves.hidden = true;
    if (results) {
      results.hidden = total === 0;
      results.innerHTML = hits.map(card).join("");
    }
    if (more) {
      if (total > hits.length) {
        more.hidden = false;
        more.textContent = "Showing " + hits.length + " of " + total + " matches.";
      } else {
        more.hidden = true;
      }
    }
    if (empty) empty.classList.toggle("show", total === 0);
    if (count) count.textContent = String(total);
  }

  if (input) input.addEventListener("input", apply);
  apply();
})();
