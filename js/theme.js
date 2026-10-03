(function () {
  var key = "wtl-theme";
  var root = document.documentElement;

  function preferred() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function current() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    var btn = document.getElementById("themeToggle");
    if (!btn) return;
    var dark = theme === "dark";
    btn.setAttribute("aria-pressed", dark ? "true" : "false");
    var label = btn.querySelector(".toggle-label");
    if (label) label.textContent = dark ? "Dark" : "Light";
  }

  var saved = null;
  try { saved = localStorage.getItem(key); } catch (e) {}
  if (saved === "light" || saved === "dark") apply(saved);
  else apply(preferred());

  var btn = document.getElementById("themeToggle");
  if (btn) {
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      try { localStorage.setItem(key, next); } catch (err) {}
      apply(next);
    });
  }

  var mq = window.matchMedia("(prefers-color-scheme: dark)");
  if (mq.addEventListener) {
    mq.addEventListener("change", function () {
      var stored = null;
      try { stored = localStorage.getItem(key); } catch (e) {}
      if (stored !== "light" && stored !== "dark") apply(preferred());
    });
  }
})();
