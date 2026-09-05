  // The hosted page: our data on Leaflet, with the Google My Map one tab away.
  // The Google one is a cross-origin iframe, so it keeps Google's styling and
  // controls; that is why both are here.
  var showNetworkMap;

  (function () {
    var host = document.getElementById("netmap");
    var raw = document.getElementById("map-data");
    if (!host || !raw || typeof L === "undefined") return;

    var data = JSON.parse(raw.textContent);
    var PALE = { city: 1, nockeby: 1, orange: 1, roslag: 1, saltsjo: 1 };
    var COLOUR = data.colours;
    var LINE = data.lineColour;

    var map = L.map(host, { zoomControl: true }).setView(data.centre, 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

    L.circle(data.centre, {
      radius: data.radius, color: "#d04139", weight: 2,
      dashArray: "8 6", fill: false, interactive: false
    }).addTo(map);

    var systems = {};
    function layerFor(name) {
      if (!systems[name]) {
        systems[name] = { lines: L.layerGroup().addTo(map),
                          stops: L.layerGroup().addTo(map), on: true };
      }
      return systems[name];
    }

    data.lines.forEach(function (line) {
      line.p.forEach(function (flat) {
        var points = [];
        for (var i = 0; i < flat.length; i += 2) points.push([flat[i], flat[i + 1]]);
        L.polyline(points, { color: COLOUR[line.c], weight: 3, opacity: .9 })
          .bindTooltip(line.n, { sticky: true })
          .addTo(layerFor(line.s).lines);
      });
    });

    var readout = document.getElementById("mapread");
    var zoneLayer = L.layerGroup();
    var dots = [];

    data.stops.forEach(function (stop) {
      var chips = stop[1].split("/").map(function (line) {
        var key = LINE[line];
        return '<span class="chip' + (PALE[key] ? " pale" : "") + '" style="background:' +
               (COLOUR[key] || "#6b7688") + ";color:" + (PALE[key] ? "#202937" : "#fff") +
               '">' + line + "</span>";
      }).join(" ");

      var marker = L.circleMarker([stop[4], stop[5]], {
        radius: 4, color: "#fff", weight: 1.5,
        fillColor: COLOUR[LINE[stop[1].split("/")[0]]] || "#6b7688", fillOpacity: 1
      }).bindPopup("<b>" + stop[0] + "</b><br>" + chips +
                   '<br><span class="kommun">' + stop[2] + " kommun</span>")
        .bindTooltip(stop[0], { direction: "top" })
        .addTo(layerFor(stop[3]).stops);

      marker.on("click", function () {
        if (readout) {
          readout.innerHTML = "<strong>" + stop[0] + "</strong> &nbsp;" + chips +
            ' &nbsp;<span class="count">' + stop[2] + " kommun</span>";
        }
      });

      dots.push(marker);
      L.circle([stop[4], stop[5]], {
        radius: data.zone, color: "#453366", weight: 1, opacity: .5,
        fillOpacity: .08, interactive: false
      }).addTo(zoneLayer);
    });

    // 235 dots at one size turn the middle of the map into a single blob
    function sizeDots() {
      var zoom = map.getZoom();
      var radius = zoom <= 9 ? 3 : zoom <= 11 ? 4 : zoom <= 13 ? 5 : 7;
      dots.forEach(function (dot) { dot.setRadius(radius); });
    }
    map.on("zoomend", sizeDots);
    sizeDots();

    Array.prototype.forEach.call(document.querySelectorAll("#mapbar .sys"), function (button) {
      var name = button.dataset.sys;
      var swatch = { "Tunnelbana": "blue", "Pendeltåg": "pendel", "Tram": "orange",
                     "Roslagsbanan": "roslag", "Saltsjöbanan": "saltsjo" }[name];
      button.style.setProperty("--swatch", COLOUR[swatch]);
      button.addEventListener("click", function () {
        var entry = systems[name];
        if (!entry) return;
        entry.on = !entry.on;
        button.setAttribute("aria-pressed", String(entry.on));
        ["lines", "stops"].forEach(function (part) {
          if (entry.on) map.addLayer(entry[part]); else map.removeLayer(entry[part]);
        });
      });
    });

    var zonesButton = document.getElementById("mapzones");
    zonesButton.addEventListener("click", function () {
      var on = zonesButton.getAttribute("aria-pressed") === "true";
      zonesButton.setAttribute("aria-pressed", String(!on));
      if (on) map.removeLayer(zoneLayer); else zoneLayer.addTo(map);
    });

    document.getElementById("mapin").addEventListener("click", function () { map.zoomIn(); });
    document.getElementById("mapout").addEventListener("click", function () { map.zoomOut(); });
    document.getElementById("mapreset").addEventListener("click", function () {
      map.setView(data.centre, 10);
    });

    // Leaflet sizes itself when it is created, so it needs telling once the panel
    // has been hidden and shown again
    showNetworkMap = function () { map.invalidateSize(); };
  })();

  (function () {
    var tabs = { net: document.getElementById("tab-net"), goo: document.getElementById("tab-goo") };
    var panels = { net: document.getElementById("panel-net"), goo: document.getElementById("panel-goo") };
    if (!tabs.net || !tabs.goo) return;
    var frame = document.getElementById("mymaps");

    function select(which) {
      Object.keys(tabs).forEach(function (key) {
        var on = key === which;
        tabs[key].setAttribute("aria-selected", String(on));
        panels[key].hidden = !on;
      });
      // the Google map costs a page load, so it waits until someone asks for it
      if (which === "goo" && frame && !frame.src) frame.src = frame.dataset.src;
      if (which === "net" && showNetworkMap) showNetworkMap();
    }

    tabs.net.addEventListener("click", function () { select("net"); });
    tabs.goo.addEventListener("click", function () { select("goo"); });
  })();
