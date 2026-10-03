(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
  var search = document.getElementById("q");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var count = document.getElementById("count");
  var empty = document.getElementById("empty");
  var cat = "all";

  function apply() {
    var q = (search && search.value ? search.value : "").trim().toLowerCase();
    var n = 0;
    cards.forEach(function (card) {
      var hay = card.getAttribute("data-hay") || "";
      var okCat = cat === "all" || card.getAttribute("data-cat") === cat;
      var okQ = !q || hay.indexOf(q) !== -1;
      var show = okCat && okQ;
      card.hidden = !show;
      if (show) n += 1;
    });
    if (count) count.textContent = String(n);
    if (empty) empty.classList.toggle("show", n === 0);
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      cat = chip.getAttribute("data-filter") || "all";
      chips.forEach(function (other) {
        other.setAttribute("aria-pressed", other === chip ? "true" : "false");
      });
      apply();
    });
  });

  if (search) search.addEventListener("input", apply);
  apply();
})();
