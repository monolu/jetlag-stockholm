  // The Artifact copy cannot load map tiles or an iframe, so it draws the network
  // from our own data: metre coordinates, pan and zoom on a transform.
  (function () {
    var svg = document.getElementById("netmap");
    var raw = document.getElementById("map-data");
    if (!svg || !raw) return;

    var data;
    try { data = JSON.parse(raw.textContent); } catch (e) { return; }

    var NS = "http://www.w3.org/2000/svg";
    var LINE_COLOUR = data.lineColour;
    var SYSTEM = {
      blue: "Tunnelbana", red: "Tunnelbana", green: "Tunnelbana",
      pendel: "Pendeltåg", city: "Tram", nockeby: "Tram", orange: "Tram",
      roslag: "Roslagsbanan", saltsjo: "Saltsjöbanan"
    };
    var CSSVAR = { red: "line-red" };
    function colourOf(line) { return LINE_COLOUR[line] || "muted"; }
    function cssColour(key) { return "var(--" + (CSSVAR[key] || key) + ")"; }

    // the payload is in metres east and south of the border centre
    var K = 111320;
    var lat0 = data.centre[0];
    function px(lat, lon) {
      return [Math.round((lon - data.centre[1]) * K * Math.cos(lat0 * Math.PI / 180)),
              Math.round(-(lat - data.centre[0]) * K)];
    }

    var R = data.radius;
    var view = { k: 1, x: 0, y: 0 };
    var picked = null;

    svg.setAttribute("viewBox", (-R) + " " + (-R) + " " + (2 * R) + " " + (2 * R));

    function make(tag, attrs) {
      var el = document.createElementNS(NS, tag);
      for (var key in attrs) el.setAttribute(key, attrs[key]);
      return el;
    }

    var root = make("g", {});
    svg.appendChild(root);
    root.appendChild(make("circle", { cx: 0, cy: 0, r: R, "class": "border" }));

    var zoneLayer = make("g", { "class": "off" });
    root.appendChild(zoneLayer);

    var lineLayer = make("g", {});
    root.appendChild(lineLayer);
    data.lines.forEach(function (line) {
      var group = make("g", {});
      group.dataset.sys = line.s;
      line.p.forEach(function (flat) {
        var points = [];
        for (var i = 0; i < flat.length; i += 2) {
          var xy = px(flat[i], flat[i + 1]);
          points.push(xy[0] + "," + xy[1]);
        }
        group.appendChild(make("polyline", {
          points: points.join(" "), "class": "route",
          stroke: cssColour(line.c), "vector-effect": "non-scaling-stroke"
        }));
      });
      lineLayer.appendChild(group);
    });

    var stopLayer = make("g", {});
    root.appendChild(stopLayer);
    var label = make("text", { "text-anchor": "middle" });

    data.stops.forEach(function (stop, i) {
      var xy = px(stop[4], stop[5]);
      var dot = make("circle", {
        cx: xy[0], cy: xy[1], r: 900, "class": "stop",
        fill: cssColour(colourOf(stop[1].split("/")[0]))
      });
      dot.dataset.i = i;
      dot.dataset.sys = stop[3];
      stopLayer.appendChild(dot);

      zoneLayer.appendChild(make("circle",
        { cx: xy[0], cy: xy[1], r: data.zone, "class": "zone" }));
    });
    root.appendChild(label);

    function apply() {
      root.setAttribute("transform",
        "translate(" + view.x + "," + view.y + ") scale(" + view.k + ")");
      svg.style.setProperty("--dot", (R / 60 / view.k) + "px");
      label.setAttribute("font-size", (R / 40 / view.k));
      label.setAttribute("stroke-width", (R / 110 / view.k));
    }

    function fit() { view = { k: 1, x: 0, y: 0 }; apply(); }

    function zoomAbout(cx, cy, factor) {
      var next = Math.min(80, Math.max(1, view.k * factor));
      if (next === view.k) return;
      view.x = cx - (cx - view.x) * (next / view.k);
      view.y = cy - (cy - view.y) * (next / view.k);
      view.k = next;
      apply();
    }

    function toLocal(event) {
      var box = svg.getBoundingClientRect();
      var side = Math.min(box.width, box.height);
      var offX = (box.width - side) / 2;
      var offY = (box.height - side) / 2;
      return {
        x: ((event.clientX - box.left - offX) / side) * 2 * R - R,
        y: ((event.clientY - box.top - offY) / side) * 2 * R - R
      };
    }

    svg.addEventListener("wheel", function (event) {
      event.preventDefault();
      var at = toLocal(event);
      zoomAbout(at.x, at.y, event.deltaY < 0 ? 1.25 : 0.8);
    }, { passive: false });

    var pointers = {};
    var last = null;
    var spread = 0;

    svg.addEventListener("pointerdown", function (event) {
      svg.setPointerCapture(event.pointerId);
      pointers[event.pointerId] = toLocal(event);
      last = toLocal(event);
      spread = 0;
      svg.classList.add("dragging");
    });

    svg.addEventListener("pointermove", function (event) {
      if (!(event.pointerId in pointers)) return;
      var here = toLocal(event);
      pointers[event.pointerId] = here;
      var ids = Object.keys(pointers);

      if (ids.length >= 2) {
        var a = pointers[ids[0]], b = pointers[ids[1]];
        var gap = Math.hypot(a.x - b.x, a.y - b.y);
        var mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
        if (spread) zoomAbout(mid.x, mid.y, gap / spread);
        spread = gap;
        return;
      }
      view.x += here.x - last.x;
      view.y += here.y - last.y;
      last = here;
      apply();
    });

    function release(event) {
      delete pointers[event.pointerId];
      spread = 0;
      if (!Object.keys(pointers).length) svg.classList.remove("dragging");
    }
    svg.addEventListener("pointerup", release);
    svg.addEventListener("pointercancel", release);

    var readout = document.getElementById("mapread");

    function show(index) {
      var stop = data.stops[index];
      var xy = px(stop[4], stop[5]);
      var chips = stop[1].split("/").map(function (line) {
        return '<span class="chip c-' + colourOf(line).replace("red", "red") + '">' + line + "</span>";
      }).join(" ");
      readout.innerHTML = "<strong>" + stop[0] + "</strong> &nbsp;" + chips +
        ' &nbsp;<span class="count">' + stop[2] + " kommun</span>";
      label.textContent = stop[0];
      label.setAttribute("x", xy[0]);
      label.setAttribute("y", xy[1] - R / 45 / view.k);
      if (picked) picked.classList.remove("pick");
      picked = stopLayer.querySelector('[data-i="' + index + '"]');
      if (picked) picked.classList.add("pick");
    }

    stopLayer.addEventListener("pointerdown", function (event) {
      var dot = event.target.closest("circle.stop");
      if (dot) show(+dot.dataset.i);
    });

    stopLayer.addEventListener("mousemove", function (event) {
      var dot = event.target.closest("circle.stop");
      if (dot) show(+dot.dataset.i);
    });

    document.getElementById("mapin").addEventListener("click", function () { zoomAbout(0, 0, 1.6); });
    document.getElementById("mapout").addEventListener("click", function () { zoomAbout(0, 0, 0.625); });
    document.getElementById("mapreset").addEventListener("click", fit);

    var zonesButton = document.getElementById("mapzones");
    zonesButton.addEventListener("click", function () {
      var on = zonesButton.getAttribute("aria-pressed") === "true";
      zonesButton.setAttribute("aria-pressed", String(!on));
      zoneLayer.classList.toggle("off", on);
    });

    Array.prototype.forEach.call(document.querySelectorAll("#mapbar .sys"), function (button) {
      var system = button.dataset.sys;
      var swatch = { "Tunnelbana": "blue", "Pendeltåg": "pendel", "Tram": "orange",
                     "Roslagsbanan": "roslag", "Saltsjöbanan": "saltsjo" }[system];
      button.style.setProperty("--swatch", cssColour(swatch));
      button.addEventListener("click", function () {
        var on = button.getAttribute("aria-pressed") === "true";
        button.setAttribute("aria-pressed", String(!on));
        Array.prototype.forEach.call(
          root.querySelectorAll('[data-sys="' + system + '"]'), function (el) {
            el.classList.toggle("off", on);
          });
      });
    });

    fit();
  })();
