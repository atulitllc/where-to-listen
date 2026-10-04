(function () {
  var search = document.getElementById("q");
  var hits = document.getElementById("hits");
  var count = document.getElementById("count");
  var empty = document.getElementById("empty");
  var shelves = document.getElementById("shelves");
  if (!search || !hits) return;
  var total = count ? count.textContent : "";
  var cache = null;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function paint(rows) {
    var q = (search.value || "").trim().toLowerCase();
    if (q.length < 2) {
      hits.hidden = true;
      hits.innerHTML = "";
      if (empty) empty.classList.remove("show");
      if (count) count.textContent = total;
      if (shelves) shelves.hidden = false;
      return;
    }
    var found = [];
    for (var i = 0; i < rows.length && found.length < 18; i++) {
      var row = rows[i];
      var hay = (row.t + " " + row.c + " " + (row.h || "")).toLowerCase();
      if (hay.indexOf(q) !== -1) found.push(row);
    }
    if (shelves) shelves.hidden = true;
    hits.hidden = false;
    hits.innerHTML = found.map(function (row) {
      return '<li><a href="podcasts/' + encodeURIComponent(row.s) + '/">' + esc(row.t) + '</a> <span>' + esc(row.c) + "</span></li>";
    }).join("");
    if (count) count.textContent = String(found.length);
    if (empty) empty.classList.toggle("show", found.length === 0);
  }

  search.addEventListener("input", function () {
    if (cache) paint(cache);
    else fetch("search.json").then(function (r) { return r.json(); }).then(function (rows) { cache = rows; paint(rows); });
  });
})();
