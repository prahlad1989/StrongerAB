/*

    $(function(){
            function MyDateField(config) {
                jsGrid.Field.call(this, config);
            };

            MyDateField.prototype = new jsGrid.Field({
                sorter: function(date1, date2) {
                    return new Date(date1) - new Date(date2);
                },

                _createDate: function(){

                    return  $("<input>").datepicker({ defaultDate: new Date() }).prop("readonly", !!this.readOnly);
                },
                filterTemplate: function() {
            if(!this.filtering)
                return "";

            var grid = this._grid,
                $result = this.filterControl = this._createDate();

            if(this.autosearch) {
                $result.on("change", function(e) {
                    grid.search();
                });
            }

            return $result;
        },


                itemTemplate: function(value) {
                    return new Date(value).toLocaleDateString();
                },

                insertTemplate: function(value) {
                    if(!this.inserting)
                        return "";
                    return this._insertPicker = $("<input>").datepicker({ defaultDate: new Date() });
                },



                editTemplate: function(value) {
                    if(!this.editing)
                        return this.itemTemplate.apply(this, arguments);
                     return this._editPicker = $("<input>").datepicker().datepicker("setDate", new Date(value));
                },

                insertValue: function() {
                    return this._insertPicker.datepicker("getDate").toISOString();
                },

                editValue: function() {
                    return this._editPicker.datepicker("getDate").toISOString();
                }
            });

            jsGrid.fields.myDateField = MyDateField;



var originalFilterTemplate = jsGrid.fields.text.prototype.filterTemplate;
            //console.log(originalFilterTemplate);
jsGrid.fields.text.prototype.filterTemplate = function() {
            var grid = this._grid;
            if(!this.filtering)
              return originalFilterTemplate;;
            var $result = originalFilterTemplate.call(this);

            $result.on("keyup", $.debounce(350,function(e) {
                  grid.search();
            }));

            return $result;
        }


    $('#jsGrid').jsGrid({
    width:"100%"    ,
    height:"550px",
    inserting:true,
    editing:true,
    sorting:true,
    paging:true,
    pageSize:11,
    autoload: true,
    filtering:true,
    autoSearch:true,
    rowClass: function(item,itemdIndex){
        if(item.is_dnd) return 'jsgrid-dnd-row';
        else return '';
    },
    controller: {
    insertItem: function(item) {
        item.csrfmiddlewaretoken='{{ csrf_token }}';
        if(!item.comments)item.comments='';
        return $.ajax({
            type: "POST",
            url: "lead",
            data: item,
            error: function (data){
                alert(data.responseJSON.error);
            },
            success: function(data){
                var $grid=$('#jsGrid');
                $grid.jsGrid("option","pageIndex",1);
                $grid.jsGrid("loadData");
            }
        });
    },

    deleteItem: function(item) {
        return $.ajax({
            type: "DELETE",
            url: "lead",
            data: JSON.stringify(item),
            headers: {"X-CSRFToken": '{{ csrf_token }}', "content-type":"text/json"}
        });
    },
    onItemInserted:function(args){
        //console.log(args);
        $("#jsGrid").jsGrid("loadData");

    }
    ,
    updateItem: function(item) {
        item.csrfmiddlewaretoken = '{{ csrf_token }}';
        return $.ajax({
            type: "PUT",
            url: "lead",
            data: JSON.stringify(item),
            headers:{"X-CSRFToken": '{{ csrf_token }}',"content-type":"text/json"},
            error:function(data){
                alert(data.responseJSON.error);
            },
            success: function(data){
                var $grid=$('#jsGrid');
                $grid.jsGrid("option","pageIndex",1);
                $grid.jsGrid("loadData");
            }
        });
    },

    loadData: function(filter) {
                        //console.log(filter.created_on);
                        var d = $.Deferred();
                        $.ajax({
                            url: "leads",
                            dataType: "json",
                            data:JSON.stringify(filter)

                        }).done(function(response) {
                            setTimeout(function() {
                                var leads=response.leads;

                                */
/*leads= $.grep(leads, function(lead) {
                return (!filter.company_name || lead.company_name.toLowerCase().indexOf(filter.company_name.toLowerCase()) > -1)
                    && (!filter.position || lead.position.toLowerCase().indexOf(filter.position.toLowerCase()) > -1 )
                    && (!filter.location || lead.location.toLowerCase().indexOf(filter.location.toLowerCase()) > -1 )
                    && (filter.is_dnd=='' || filter.is_dnd === undefined || lead.is_dnd === filter.is_dnd)
                    && (filter.is_client=='' || filter.is_client === undefined || lead.is_client === filter.is_client)
                    //&& (filter.lead_age === undefined || lead.lead_age === undefined ||  lead.lead_age === filter.lead_age)
                    && (filter.portals=='' || filter.portals === undefined || lead.portals === filter.portals)
                    && (!filter.created_by__username || lead.created_by__username.toLowerCase().indexOf(filter.created_by__username.toLowerCase()) > -1)
                    && (!filter.created_on || lead.created_on === filter.created_on)
                    && (!filter.comments || lead.comments.toLowerCase().indexOf(filter.comments.toLowerCase()) > -1 )
                   ;
            });*//*

                                d.resolve(leads);
                            }, 2000);
                        });

                        return d.promise();
                    }
                },


    fields: [
        {title: "Id", name: "id", type: "number", visible: false, inserting: false, editing: false },
        {title: "Company", name: "company_name", type: "text", validate: "required",width:150 },
        {title: "Position", name: "position", type: "text", validate: "required",width:125 },
        {title: "Location", name: "location", type: "text", validate: "required",width:125},
        {title: "Portals", name: "portals", type: "select",validate: "required",width:75, items: portals ,valueField: "Name", textField: "Name"},
        {title: "Lead Age",name: "created_on", type: "text",width:50, itemTemplate:function(value,item){var secs= Math.abs(new Date()-new Date(value));
          return days=Math.floor(secs/(24*60*60*1000));
        },inserting:false, editing: false,filtering:false },

        {title: "Is DND", name: "is_dnd", type: "checkbox", sorting: false,width:50, inserting: is_user_staff, editing: is_user_staff },
        {title: "Is Client",name: "is_client", type: "checkbox", sorting: false,width:50, inserting: is_user_staff, editing: is_user_staff },
        //{title: "Created at",name: "created_at", type: "text",readOnly:true, inserting: false, editing: false },
        //{title: "Updated at",name: "updated_at", type: "text", readOnly:true, inserting: false, editing: false },
        {title: "Created on",name: "created_on", type: "myDateField", width:80, align: "center", inserting: false, editing: false ,filtering:false}
   ,
        {title: "Analyst",name: "created_by__username", type: "text", valueField: "created_by", textField: "created_by__username",filtering: true,inserting: false, editing: false },
        {title: "Comments", name: "comments", type: "textarea", inserting:true},
        {title: "Created By", name: "created_by", type:"number", visible:false,inserting: false, editing: false },
        {type: "control" }
    ]

    });

});
*/
