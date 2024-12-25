var app = angular.module('useCaseDiagramApp', []);

app.controller('DiagramController', function($scope) {
  var $ = go.GraphObject.make;
  var myDiagram = $(go.Diagram, "myDiagramDiv",
    {
      "undoManager.isEnabled": true,
      layout: $(go.TreeLayout, { angle: 90, layerSpacing: 35 })
    }
  );

  myDiagram.nodeTemplate = $(go.Node, "Auto",
    $(go.Shape, "RoundedRectangle", { fill: "white" }),
    $(go.TextBlock, { margin: 5 },
      new go.Binding("text", "key"))
  );

  myDiagram.linkTemplate = $(go.Link,
    { routing: go.Link.Orthogonal, corner: 10 },
    $(go.Shape),
    $(go.Shape, { toArrow: "Standard" })
  );

  var nodeDataArray = [
    { key: "Belle Croissant Lyonnais System" },
    { key: "Baker" },
    { key: "Cashier" },  
    { key: "Manager" },
    { key: "Loyal Customer" },
    { key: "Tourist" },
    { key: "Manage Inventory" },
    { key: "Manage Recipes" },
    { key: "Process Orders" },
    { key: "Apply Discounts" },
    { key: "Track Sales" },
    { key: "Manage Staff" },  
    { key: "Browse Menu" },
    { key: "Place Orders" },
    { key: "Earn Loyalty Points" }
  ];

  var linkDataArray = [
    { from: "Belle Croissant Lyonnais System", to: "Manage Inventory" },
    { from: "Belle Croissant Lyonnais System", to: "Manage Recipes" },
    { from: "Belle Croissant Lyonnais System", to: "Process Orders" },
    { from: "Belle Croissant Lyonnais System", to: "Apply Discounts" },
    { from: "Belle Croissant Lyonnais System", to: "Track Sales" },
    { from: "Belle Croissant Lyonnais System", to: "Manage Staff" },
    { from: "Belle Croissant Lyonnais System", to: "Browse Menu" },
    { from: "Belle Croissant Lyonnais System", to: "Place Orders" },
    { from: "Belle Croissant Lyonnais System", to: "Earn Loyalty Points" },
    { from: "Baker", to: "Manage Inventory" }, 
    { from: "Baker", to: "Manage Recipes" },
    { from: "Cashier", to: "Process Orders" },
    { from: "Cashier", to: "Apply Discounts" },  
    { from: "Manager", to: "Track Sales" },
    { from: "Manager", to: "Manage Staff" },
    { from: "Loyal Customer", to: "Browse Menu" },
    { from: "Loyal Customer", to: "Place Orders" },
    { from: "Loyal Customer", to: "Earn Loyalty Points" },
    { from: "Tourist", to: "Browse Menu" },  
    { from: "Tourist", to: "Place Orders" }
  ];

  myDiagram.model = new go.GraphLinksModel(nodeDataArray, linkDataArray);
});